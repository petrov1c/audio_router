"""
Синтез аудио для тестового датасета.
Использует Qwen3-TTS для генерации речи.
"""

import json
import argparse
import torch
import soundfile
import librosa
from pathlib import Path
from typing import List, Dict

from qwen_tts.inference.qwen3_tts_model import Qwen3TTSModel
from tqdm import tqdm


# ANCHOR:qwen3_tts_synthesizer
class Qwen3TTSSynthesizer:
    """Синтезатор аудио с использованием Qwen3-TTS."""
    
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        device: str = None
    ):
        """
        Инициализация синтезатора.
        
        Args:
            model_name: Имя модели на Hugging Face.
            device: Устройство для вычислений (cuda/cpu).
        """
        self.model_name = model_name
        
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        print(f"Используется устройство: {self.device}")
        self.model = None
        self.sample_rate = 16000

    def _init_model(self):
        """Инициализировать модель TTS."""
        if self.model is not None:
            return
        
        try:
            print(f"Загрузка модели: {self.model_name}")
            self.model = Qwen3TTSModel.from_pretrained(
                self.model_name,
                device_map=self.device,
                trust_remote_code=True,
                dtype=torch.bfloat16 if self.device == "cuda" else torch.float32
            )
            
            print("✓ Модель загружена")
            
        except ImportError:
            print("❌ Ошибка: библиотека transformers не установлена")
            print("Установите: pip install transformers torch qwen-tts")
            raise
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            raise
    
    def synthesize(
        self,
        text: str,
        output_path: str,
        speaker: str = 'Aiden',
    ) -> bool:
        """
        Синтезировать аудио для текста.
        
        Args:
            text: Текст для синтеза.
            output_path: Путь для сохранения аудио.
            speaker: Спикер.

        Returns:
            True если успешно, False иначе.
        """
        try:
            self._init_model()
            
            # Генерация аудио
            audio, sr = self.model.generate_voice_design(
                text = text,
                language='Russian',
                instruct='Используй мягкий тон. Говори спокойно',
            )

            # Сохранение аудио
            if audio is not None:
                audio = librosa.resample(
                    audio[0],
                    orig_sr=sr,
                    target_sr=self.sample_rate
                )
                soundfile.write(output_path, audio, samplerate=self.sample_rate, format="WAV")
                return True
            else:
                print(f"⚠️  Не удалось извлечь аудио для: {text[:50]}...")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка синтеза для '{text[:50]}...': {e}")
            return False
# END:qwen3_tts_synthesizer


# ANCHOR:audio_synthesizer
class AudioSynthesizer:
    """Синтезатор аудио для датасета."""
    
    def __init__(
        self,
        dataset_path: str,
        output_dir: str = "data/datasets/audio",
        model_name: str = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        device: str = None,
    ):
        """
        Инициализация синтезатора.
        
        Args:
            dataset_path: Путь к JSON файлу с датасетом.
            output_dir: Директория для сохранения аудио файлов.
            model_name: Имя модели TTS.
            device: Устройство для вычислений.
        """
        self.dataset_path = Path(dataset_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Загружаем датасет
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            self.dataset: List[Dict] = json.load(f)
        
        print(f"Загружен датасет: {len(self.dataset)} примеров")
        
        # Инициализируем TTS
        self.tts = Qwen3TTSSynthesizer(model_name=model_name, device=device)
    
    def synthesize_all(self, alternate_speakers: bool = True) -> None:
        """
        Синтезировать аудио для всех примеров в датасете.
        
        Args:
            alternate_speakers: Чередовать голоса для разнообразия.
        """
        print(f"\nСинтез аудио для {len(self.dataset)} примеров...")
        print(f"Выходная директория: {self.output_dir}")
        
        updated_dataset = []
        success_count = 0
        fail_count = 0

        speakers = ['Aiden', 'Serena', 'Ryan']
        for idx, item in enumerate(tqdm(self.dataset, desc="Синтез аудио")):
            item_id = item['id']
            text = item['text']
            
            # Путь к аудио файлу
            audio_filename = f"{item_id}.wav"
            audio_path = self.output_dir / audio_filename
            
            # Чередуем голоса для разнообразия
            speaker = speakers[idx % 3] if alternate_speakers else speakers[0]
            
            try:
                # Синтезируем аудио
                success = self.tts.synthesize(
                    text=text,
                    output_path=str(audio_path),
                    speaker=speaker
                )
                
                if success:
                    # Обновляем запись в датасете
                    item['audio_path'] = str(audio_path)
                    item['audio_synthesized'] = True
                    success_count += 1
                else:
                    item['audio_path'] = None
                    item['audio_synthesized'] = False
                    fail_count += 1
                
            except Exception as e:
                print(f"\n❌ Ошибка синтеза для {item_id}: {e}")
                item['audio_path'] = None
                item['audio_synthesized'] = False
                fail_count += 1
            
            updated_dataset.append(item)
        
        # Сохраняем обновленный датасет
        output_path = self.dataset_path.parent / f"{self.dataset_path.stem}_with_audio.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_dataset, f, ensure_ascii=False, indent=2)
        
        # Статистика
        print(f"\n{'='*60}")
        print("РЕЗУЛЬТАТЫ СИНТЕЗА")
        print(f"{'='*60}")
        print(f"✓ Успешно синтезировано: {success_count}/{len(updated_dataset)}")
        print(f"✗ Ошибок:                {fail_count}/{len(updated_dataset)}")
        print(f"✓ Обновленный датасет:   {output_path}")
# END:audio_synthesizer


# ANCHOR:main
def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(description="Синтез аудио для датасета")
    parser.add_argument(
        "--input",
        type=str,
        default="data/datasets/evaluation_dataset.json",
        help="Путь к входному датасету"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/datasets/audio",
        help="Директория для аудио файлов"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        help="Имя TTS модели"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Устройство (cuda/cpu)"
    )
    parser.add_argument(
        "--no-alternate-speakers",
        action="store_true",
        help="Не чередовать голоса"
    )
    
    args = parser.parse_args()
    
    # Создаем синтезатор с Qwen3-TTS
    synthesizer = AudioSynthesizer(
        dataset_path=args.input,
        output_dir=args.output,
        model_name=args.model,
        device=args.device,
    )
        
    # Синтезируем аудио
    synthesizer.synthesize_all(alternate_speakers=not args.no_alternate_speakers)
    
    print("\nГотово!")


if __name__ == "__main__":
    main()
# END:main
