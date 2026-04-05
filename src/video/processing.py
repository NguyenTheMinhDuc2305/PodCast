from moviepy.editor import CompositeAudioClip, ImageClip, AudioFileClip, TextClip, CompositeVideoClip, VideoFileClip, concatenate_videoclips, VideoFileClip
import moviepy.video.fx.all as vfx
from moviepy.audio import fx as afx
import json
import os
import re
import tempfile
from moviepy.config import change_settings
from pathlib import Path
# from 
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip

from src.image.processing import add_highlight_bullets_to_image, load_image


def _highlight_row_from_payload(highlight: object) -> dict:
    """
    ``highlight`` từ ``generate_script`` là JSON string: thường là ``[{...}]``
    (list một dict), hoặc đôi khi một dict — lấy dict dòng đầu để đọc ``highlight_*_title``.
    """
    if highlight is None:
        return {}
    if isinstance(highlight, dict):
        return highlight
    if isinstance(highlight, list):
        if highlight and isinstance(highlight[0], dict):
            return highlight[0]
        return {}
    if isinstance(highlight, str):
        s = highlight.strip()
        if not s:
            return {}
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            return {}
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
        if isinstance(data, dict):
            return data
        return {}
    return {}


def create_video_from_image(image_path, audio_path, script, output_path):

    # 1. Tải âm thanh và hình ảnh
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    image_clip = ImageClip(image_path).set_duration(audio_duration)

    # --- CẤU HÌNH NGẮT DÒNG ---
    # Bạn hãy tùy chỉnh con số này. Nếu chữ to, giảm số này xuống (VD: 12, 15). 
    # Nếu chữ nhỏ, tăng lên (VD: 20, 25) để vừa vặn 2 dòng của bạn.
    so_tu_toi_da_mot_man_hinh = 16 
    
    khung_rong = image_clip.w - 120
    khung_cao = 249
    # --------------------------

    # 2. Xử lý tách câu và Tách đoạn (Chunking)
    raw_sentences = re.split(r'(?<=[.!?\n])\s+', script.strip())
    raw_sentences = [s for s in raw_sentences if s.strip()]

    # Tạo danh sách các "đoạn nhỏ" (chunks). 
    # Nếu câu ngắn -> là 1 đoạn. Nếu câu dài -> bị cắt thành nhiều đoạn.
    chunks = []
    for sentence in raw_sentences:
        words_in_sentence = sentence.split()
        if not words_in_sentence:
            continue
        
        # Cắt câu dài thành các nhóm nhỏ dựa trên số từ tối đa
        for i in range(0, len(words_in_sentence), so_tu_toi_da_mot_man_hinh):
            chunk = words_in_sentence[i : i + so_tu_toi_da_mot_man_hinh]
            chunks.append(chunk)

    # Tính thời gian cho mỗi từ dựa trên TỔNG số từ của cả kịch bản
    total_words = len(script.split())
    time_per_word = audio_duration / total_words if total_words > 0 else 0

    text_clips = []
    current_time = 0 

    # 3. Vòng lặp TẦNG 1: Lặp qua từng "đoạn nhỏ" (chunk)
    for chunk_words in chunks:
        # Tính toán thời gian bắt đầu và kết thúc của nguyên ĐOẠN này
        chunk_start_time = current_time
        chunk_duration = len(chunk_words) * time_per_word
        chunk_end_time = chunk_start_time + chunk_duration
        
        current_text = "" # Biến này reset về rỗng -> XÓA SẠCH màn hình để viết đoạn mới
        
        # 4. Vòng lặp TẦNG 2: Lặp qua từng từ trong đoạn
        for i, word in enumerate(chunk_words):
            current_text += word + " "

            txt_clip = TextClip(
                current_text.strip(),
                fontsize=45,
                color='#333333',
                font="E:/WORK/PodCast/src/inputs/font/Be_Vietnam_Pro/BeVietnamPro-SemiBold.ttf",
                size=(khung_rong, khung_cao), 
                method="caption",
                align="NorthWest" 
            )

            # Tính thời gian hiển thị của TỪ này
            word_start_time = chunk_start_time + i * time_per_word
            
            if i < len(chunk_words) - 1:
                word_end_time = chunk_start_time + (i + 1) * time_per_word
            else:
                word_end_time = chunk_end_time
            
            txt_clip = (
                txt_clip.set_position(("center", "bottom"))
                .set_start(word_start_time)
                .set_end(word_end_time)
            )
            text_clips.append(txt_clip)
            
        # Cập nhật mốc thời gian cho đoạn tiếp theo
        current_time = chunk_end_time

    # 5. Xếp chồng ảnh và text, lồng audio
    video = CompositeVideoClip([image_clip] + text_clips)
    video = video.set_audio(audio_clip)
    
    # 6. Xuất file và dọn dẹp
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    audio_clip.close()
    video.close()
    image_clip.close()

    for clip in text_clips:
        clip.close()

def combine_video(video_paths, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video_clips = []
    for path in video_paths:
        if os.path.exists(path):
            clip = VideoFileClip(path)
            video_clips.append(clip)
        
        else:
            print(f"File {path} không tồn tại. Bỏ qua.")
    
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    for clip in video_clips:
        clip.close()    
    final_video.close()

def create_intro_part(audio_path, script, output_path, image_path):
    create_video_from_image(image_path, audio_path, script, output_path)

def create_highlight_part(audio_path, script, output_path, image_path, highlight):
    """
    ``highlight``: JSON string (vd ``convert_d2t(get_highlight(...))``) — format ``[{...}]``
    với các key ``highlight_1_title``, … — parse trong hàm, không đổi ``generate_script``.
    """
    row = _highlight_row_from_payload(highlight)
    overlay_path = str(
        Path(output_path).with_name(f"{Path(output_path).stem}_frame.png")
    )
    frame = load_image(image_path)
    if frame.mode not in ("RGB", "RGBA"):
        frame = frame.convert("RGBA")
    add_highlight_bullets_to_image(frame, row, overlay_path)
    create_video_from_image(overlay_path, audio_path, script, output_path)


def create_improve_part(audio_path, script, output_path, image_path, improve):
    create_video_from_image(image_path, audio_path, script, output_path)

def create_final_part(audio_path, script, output_path, image_paths):
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration

    first_path = ImageClip(image_paths[0]).set_duration(audio_duration/2.0)
    second_path = ImageClip(image_paths[1]).set_duration(audio_duration/2.0)

    video = concatenate_videoclips([first_path, second_path], method="compose")

    video = video.set_audio(audio_clip)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    audio_clip.close()
    video.close()
    first_path.close()
    second_path.close()


def add_background_music(
    video_path,
    music_path,
    output_path,
    music_volume: float = 0.2,
    loop_music: bool = True,
) -> None:
    """
    Mix nhạc nền vào audio của video.

    Nếu ``output_path`` trùng ``video_path``, ghi ra file tạm rồi ``os.replace``
    để tránh đọc/ghi cùng một file (dễ hỏng file trên Windows).
    """
    video_path = Path(video_path)
    music_path = Path(music_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    video = VideoFileClip(str(video_path))
    voice = video.audio
    if voice is None:
        video.close()
        raise ValueError("Video không có track audio; không thể mix nhạc nền.")

    music = AudioFileClip(str(music_path)).volumex(music_volume)
    if music.duration < video.duration and loop_music:
        music = afx.audio_loop(music, duration=video.duration)
    else:
        music = music.subclip(0, min(music.duration, video.duration))

    final_audio = CompositeAudioClip([voice, music]).set_duration(video.duration)
    out = video.set_audio(final_audio)

    same_file = video_path.resolve() == output_path.resolve()
    if same_file:
        fd, tmp_str = tempfile.mkstemp(
            suffix=".mp4", prefix="bgm_", dir=str(output_path.parent)
        )
        os.close(fd)
        write_path = Path(tmp_str)
    else:
        write_path = output_path

    try:
        out.write_videofile(
            str(write_path),
            codec="libx264",
            audio_codec="aac",
            fps=video.fps if video.fps else 24,
        )
    finally:
        out.close()
        final_audio.close()
        music.close()
        video.close()

    if same_file:
        os.replace(write_path, output_path)
if __name__ == "__main__":
    image_path = "1.jpg"
    audio = "Mở đầu.m4a"
    caunoi = "Dạ, Chào ba mẹ Hải Yến! Cô Thu Hà đây ạ. Tháng 11 vừa rồi Yến có nhiều chuyển biến thú vị lắm đặc biệt sự thay đổi kỹ năng Viết, vì vậy cô xin gửi đến ba mẹ một bản bản tin ngắn tổng hợp lại hành trình học tập đầy ấn tượng của con trong tháng vừa qua để ba mẹ cùng chia vui với những nỗ lực tuyệt vời của con nhé!"
    output_path = "output1.mp4"
    create_video_from_image(image_path, audio, caunoi, output_path)