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

from src.image.processing import (
    add_highlight_bullets_to_image,
    add_improve_bullets_to_image,
    load_image,
)

# Độ dài đoạn **chỉ hình** (sau khi thoại đã hết) rồi mới fade — ghép vào mỗi đoạn trừ đoạn cuối
DEFAULT_COMBINE_SEGMENT_END_FADE_SECONDS = 1.0

# Không ghép đuôi fade giữa hai phần liền kề (theo stem tên file, vd improve.mp4 → solution.mp4)
DEFAULT_SKIP_FADE_BETWEEN_STEMS: frozenset[tuple[str, str]] = frozenset(
    {("improve", "solution")}
)


def _append_fade_tail_after_clip(clip: VideoFileClip, fade_seconds: float) -> VideoFileClip:
    """
    Khi ghép nhiều đoạn: thoại/audio của đoạn phát **hết trước**, sau đó mới thêm
    vài giây chỉ có **hình** (frame cuối) rồi fade-out — không chồng fade lên lúc đang nói.

    Đoạn đuôi không có audio (im lặng); đoạn tiếp theo bắt đầu sau khi fade xong.
    """
    d = float(clip.duration or 0)
    if fade_seconds <= 0 or d <= 0.05:
        return clip
    fd = float(fade_seconds)
    fps = float(clip.fps or 24)
    last_t = max(0.0, min(d - 1e-3, d - 1.0 / max(fps, 1.0)))
    try:
        frame = clip.get_frame(last_t)
    except Exception:
        try:
            frame = clip.get_frame(0.0)
        except Exception:
            return clip

    tail = ImageClip(frame).set_duration(fd).set_fps(fps)
    tail = tail.fx(vfx.fadeout, fd)
    w, h = clip.size
    if (tail.w, tail.h) != (w, h):
        tail = tail.resize((w, h))

    return concatenate_videoclips([clip, tail], method="compose")


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


def create_video_from_image(
    image_path,
    audio_path,
    script,
    output_path,
    height=250,
    width_change=120,
    *,
    text_speed_multiplier: float = 1.02,
):

    # 1. Tải âm thanh và hình ảnh
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    image_clip = ImageClip(image_path).set_duration(audio_duration)

    # --- CẤU HÌNH NGẮT DÒNG ---
    # Bạn hãy tùy chỉnh con số này. Nếu chữ to, giảm số này xuống (VD: 12, 15). 
    # Nếu chữ nhỏ, tăng lên (VD: 20, 25) để vừa vặn 2 dòng của bạn.
    so_tu_toi_da_mot_man_hinh = 16 
    
    khung_rong = image_clip.w - width_change
    khung_cao = height
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
    # Có thể tăng tốc "chạy chữ" bằng text_speed_multiplier > 1.0 (chữ hiện nhanh hơn audio).
    total_words = len(script.split())
    speed = float(text_speed_multiplier or 1.0)
    if speed <= 0:
        speed = 1.0
    base_time_per_word = audio_duration / total_words if total_words > 0 else 0
    time_per_word = base_time_per_word / speed if base_time_per_word > 0 else 0

    text_clips = []
    current_time = 0 
    last_text_clip = None

    # 3. Vòng lặp TẦNG 1: Lặp qua từng "đoạn nhỏ" (chunk)
    for chunk_words in chunks:
        # Tính toán thời gian bắt đầu và kết thúc của nguyên ĐOẠN này
        chunk_start_time = current_time
        chunk_duration = len(chunk_words) * time_per_word
        chunk_end_time = chunk_start_time + chunk_duration
        if chunk_start_time >= audio_duration:
            break
        chunk_end_time = min(chunk_end_time, audio_duration)
        
        current_text = "" # Biến này reset về rỗng -> XÓA SẠCH màn hình để viết đoạn mới
        
        # 4. Vòng lặp TẦNG 2: Lặp qua từng từ trong đoạn
        for i, word in enumerate(chunk_words):
            current_text += word + " "

            txt_clip = TextClip(
                current_text.strip(),
                fontsize=50,
                color='#333333',
                font="E:/WORK/PodCast/src/inputs/font/Nutri/static/Nunito-Bold.ttf",
                size=(khung_rong, khung_cao), 
                method="caption",
                align="NorthWest" 
            )

            # Tính thời gian hiển thị của TỪ này
            word_start_time = chunk_start_time + i * time_per_word
            if word_start_time >= audio_duration:
                break
            
            if i < len(chunk_words) - 1:
                word_end_time = chunk_start_time + (i + 1) * time_per_word
            else:
                word_end_time = chunk_end_time
            word_end_time = min(word_end_time, audio_duration)
            if word_end_time <= word_start_time:
                continue
            
            txt_clip = (
                txt_clip.set_position(("center", "bottom"))
                .set_start(word_start_time)
                .set_end(word_end_time)
            )
            text_clips.append(txt_clip)
            last_text_clip = txt_clip
            
        # Cập nhật mốc thời gian cho đoạn tiếp theo
        current_time = chunk_end_time
        if current_time >= audio_duration:
            break

    # Nếu chạy chữ nhanh hơn audio: giữ nguyên text cuối đến hết audio.
    if last_text_clip is not None and float(last_text_clip.end or 0) < audio_duration:
        hold = last_text_clip.copy().set_start(float(last_text_clip.end)).set_end(audio_duration)
        text_clips.append(hold)

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

def combine_video(
    video_paths,
    output_path,
    *,
    segment_end_fade_seconds: float | None = None,
    skip_fade_between_stems: frozenset[tuple[str, str]] | None = None,
):
    """
    Ghép các video theo thứ tự.

    Mặc định: sau khi **thoại hết** ở mỗi đoạn (trừ đoạn **cuối cùng**), ghép thêm một
    đoạn ngắn chỉ có hình (frame cuối) rồi **fade-out** — không fade trong lúc đang nói.
    Đặt ``segment_end_fade_seconds=0`` để tắt.

    Có thể **bỏ qua** fade giữa hai phần liền kề (theo stem file .mp4), ví dụ
    ``improve`` → ``solution`` — dùng ``skip_fade_between_stems`` hoặc mặc định
    ``DEFAULT_SKIP_FADE_BETWEEN_STEMS``.

    Args:
        video_paths: Danh sách đường dẫn file .mp4.
        output_path: File output.
        segment_end_fade_seconds: Độ dài đuôi chỉ-hình + fade (giây); ``None`` = dùng
            ``DEFAULT_COMBINE_SEGMENT_END_FADE_SECONDS``.
        skip_fade_between_stems: Tập các cặp ``(stem_trước, stem_sau)`` không thêm đuôi fade
            ở ranh giới đó; ``None`` = dùng ``DEFAULT_SKIP_FADE_BETWEEN_STEMS``;
            ``frozenset()`` rỗng = luôn fade mọi chỗ (trừ quy tắc đoạn cuối).
    """
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    fade_s = (
        DEFAULT_COMBINE_SEGMENT_END_FADE_SECONDS
        if segment_end_fade_seconds is None
        else float(segment_end_fade_seconds)
    )

    skip_pairs = (
        DEFAULT_SKIP_FADE_BETWEEN_STEMS
        if skip_fade_between_stems is None
        else skip_fade_between_stems
    )

    video_clips: list[VideoFileClip] = []
    valid_paths: list[str] = []
    for path in video_paths:
        if os.path.exists(path):
            video_clips.append(VideoFileClip(path))
            valid_paths.append(path)
        else:
            print(f"File {path} không tồn tại. Bỏ qua.")

    if not video_clips:
        print("Không có clip hợp lệ để ghép.")
        return

    n = len(video_clips)
    for i in range(n - 1):
        if fade_s <= 0:
            break
        stem_before = Path(valid_paths[i]).stem
        stem_after = Path(valid_paths[i + 1]).stem
        if (stem_before, stem_after) in skip_pairs:
            continue
        video_clips[i] = _append_fade_tail_after_clip(video_clips[i], fade_s)

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    for clip in video_clips:
        clip.close()
    final_video.close()

def create_intro_part(audio_path, script, output_path, image_path):
    create_video_from_image(image_path, audio_path, script, output_path, width_change= 150)

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
    create_video_from_image(overlay_path, audio_path, script, output_path, height= 230, width_change= 150)


def create_improve_part(audio_path, script, output_path, image_path, improve_lines):
    """
    ``improve_lines``: list 3 chuỗi — vẽ bullet lên ảnh rồi render (giống ``create_highlight_part``).
    """
    # improve_lines = improve_lines.split(".. ")
    if not isinstance(improve_lines, list):
        improve_lines = list(improve_lines) if improve_lines else []
    overlay_path = str(
        Path(output_path).with_name(f"{Path(output_path).stem}_frame.png")
    )
    frame = load_image(image_path)
    if frame.mode not in ("RGB", "RGBA"):
        frame = frame.convert("RGBA")
    add_improve_bullets_to_image(frame, improve_lines, overlay_path)
    create_video_from_image(
        overlay_path, audio_path, script, output_path, height=200, width_change=150
    )

def create_solution_part(audio_path, script, output_path, image_path):
    create_video_from_image(image_path, audio_path, script, output_path, height= 200, width_change= 150)

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