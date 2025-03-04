# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu, Liu Yue)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import random
import sys
import gradio as gr
import librosa
import numpy as np
import torch

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append('{}/third_party/Matcha-TTS'.format(ROOT_DIR))
from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav, logging
from cosyvoice.utils.common import set_all_random_seed

inference_mode_list = ['3s极速复刻', '跨语种复刻', '自然语言控制']
instruct_dict = {'预训练音色': '1. 选择预训练音色\n2. 点击生成音频按钮',
                 '3s极速复刻': '简单音色复刻:\n1. 选择prompt音频文件，或录入prompt音频，注意不超过30s，若同时提供，优先选择prompt音频文件\n2. 输入prompt文本\n3. 点击生成音频按钮',
                 '跨语种复刻': '支持语气指令复刻音色:\n1. 选择prompt音频文件，或录入prompt音频，注意不超过30s，若同时提供，优先选择prompt音频文件\n2. 点击生成音频按钮',
                 '自然语言控制': '支持方言复刻音色:\n1. 选择prompt音频文件，或录入prompt音频，注意不超过30s，若同时提供，优先选择prompt音频文件\n2. 输入instruct文本\n3. 点击生成音频按钮'}
stream_mode_list = [('否', False), ('是', True)]
max_val = 0.8


def generate_seed():
    seed = random.randint(1, 100000000)
    return {
        "__type__": "update",
        "value": seed
    }


def postprocess(speech, top_db=60, hop_length=220, win_length=440):
    speech, _ = librosa.effects.trim(
        speech, top_db=top_db,
        frame_length=win_length,
        hop_length=hop_length
    )
    if speech.abs().max() > max_val:
        speech = speech / speech.abs().max() * max_val
    speech = torch.concat([speech, torch.zeros(1, int(cosyvoice.sample_rate * 0.2))], dim=1)
    return speech


def change_instruction(mode_checkbox_group):
    return instruct_dict[mode_checkbox_group]


def generate_audio(tts_text, mode_checkbox_group, prompt_text, prompt_wav_upload, instruct_text = None,
                   seed = 0, stream = False, speed = 1):
    if prompt_wav_upload is not None:
        prompt_wav = prompt_wav_upload
    else:
        prompt_wav = None
    # elif prompt_wav_record is not None:
    #     prompt_wav = prompt_wav_record

    if mode_checkbox_group == '3s极速复刻':
        logging.info('get zero_shot inference request')
        prompt_speech_16k = postprocess(load_wav(prompt_wav, prompt_sr))
        set_all_random_seed(seed)
        outaudio = None
        for i in cosyvoice.inference_zero_shot(tts_text, prompt_text, prompt_speech_16k, stream=stream, speed=speed):
            audio = i['tts_speech'].numpy().flatten()
            if outaudio is None:
                outaudio = audio
            else:
                outaudio = np.concatenate([outaudio, audio])
            yield (cosyvoice.sample_rate, outaudio)
    elif mode_checkbox_group == '跨语种复刻':
        logging.info('get cross_lingual inference request')
        prompt_speech_16k = postprocess(load_wav(prompt_wav, prompt_sr))
        set_all_random_seed(seed)
        outaudio = None
        for i in cosyvoice.inference_cross_lingual(tts_text, prompt_speech_16k, stream=stream, speed=speed):
            audio = i['tts_speech'].numpy().flatten()
            if outaudio is None:
                outaudio = audio
            else:
                outaudio = np.concatenate([outaudio, audio])
            yield (cosyvoice.sample_rate, outaudio)
    else:
        logging.info('get instruct inference request')
        set_all_random_seed(seed)
        prompt_speech_16k = postprocess(load_wav(prompt_wav, prompt_sr))
        outaudio = None
        for i in cosyvoice.inference_instruct2(tts_text, instruct_text, prompt_speech_16k=prompt_speech_16k, stream=stream, speed=speed):
            audio = i['tts_speech'].numpy().flatten()
            if outaudio is None:
                outaudio = audio
            else:
                outaudio = np.concatenate([outaudio, audio])
            yield (cosyvoice.sample_rate, outaudio)


def main():
    css = """
    # .border-css {
    #     border: 1px solid #e6e6e6;
    #     border-radius: 5px;
    #     padding: 10px;
    # }
    """
    # theme = gr.Theme.from_hub('ParityError/Interstellar')
    with gr.Blocks(css=css, theme=gr.themes.Soft(), title="CosyVoice2") as demo:
        gr.Markdown("### 代码库 [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) \
                    预训练模型 [CosyVoice2-0.5B](https://www.modelscope.cn/models/iic/CosyVoice2-0.5B)")
        gr.Markdown("#### 请输入需要合成的文本，选择推理模式，并按照提示步骤进行操作")

        tts_text = gr.Textbox(label="输入合成文本", lines=1, value="我是通义实验室语音团队全新推出的生成式语音大模型，提供舒适自然的语音合成能力。", elem_classes='border-css')

        with gr.Row(elem_classes='border-css'):
            with gr.Column(scale=4):
                with gr.Row():
                    with gr.Column(scale=4):
                        mode_checkbox_group = gr.Radio(choices=inference_mode_list, label='选择推理模式', value=inference_mode_list[0])
                    with gr.Column(scale=1):
                        stream = gr.Radio(choices=stream_mode_list, label='是否流式推理', value=stream_mode_list[0][1])
                    with gr.Column(scale=1):
                        speed = gr.Number(value=1, label="速度调节(仅支持非流式推理)", minimum=0.5, maximum=2.0, step=0.1)

            with gr.Column(scale=1):
                seed_button = gr.Button(value="\U0001F3B2")
                seed = gr.Number(value=0, label="随机推理种子")

        with gr.Row():
            instruction_text = gr.Text(label="操作步骤", value=instruct_dict[inference_mode_list[0]])

        with gr.Row():
            prompt_wav_upload = gr.Audio(sources=['upload', 'microphone'], type='filepath', label='上传音频文件，注意采样率不低于16khz')

        # with gr.Row():
        #     prompt_wav_record = gr.Audio(sources='microphone', type='filepath', label='录制prompt音频文件')

        prompt_text = gr.Textbox(label="输入prompt文本", lines=1, placeholder="请输入prompt文本，需与prompt音频内容一致，暂时不支持自动识别...", value='')
        instruct_text = gr.Textbox(label="输入instruct文本", lines=1, placeholder="请输入instruct文本.", value='')

        generate_button = gr.Button("生成音频")

        audio_output = gr.Audio(label="合成音频")

        seed_button.click(generate_seed, inputs=[], outputs=seed)
        generate_button.click(generate_audio,
                              inputs=[tts_text, mode_checkbox_group, prompt_text, prompt_wav_upload,
                                      instruct_text, seed, stream, speed],
                              outputs=[audio_output])
        mode_checkbox_group.change(fn=change_instruction, inputs=[mode_checkbox_group], outputs=[instruction_text])
    demo.queue(max_size=4, default_concurrency_limit=2)
    demo.launch(server_name='0.0.0.0')


if __name__ == '__main__':
    try:
        cosyvoice = CosyVoice2('pretrained_models/CosyVoice2-0.5B')
    except Exception:
        raise TypeError('no valid model_type!')

    sft_spk = cosyvoice.list_available_spks()
    if len(sft_spk) == 0:
        sft_spk = ['']
    prompt_sr = 16000
    default_data = np.zeros(cosyvoice.sample_rate)
    main()
