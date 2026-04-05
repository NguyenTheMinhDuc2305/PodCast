from src.audio import load_audio_model
from src.text import load_text_model
from src.utils.query import get_highlight, get_content, get_improve, get_name, get_teacher, get_class
import os
from src.image.processing import load_image, add_information_to_intro_image
from src.video.processing import create_video_from_image, combine_video, create_intro_part, create_highlight_part, create_improve_part, create_final_part, add_background_music
from src.utils.config import mapping_script2image
from src.utils.convert_d2t import convert_d2t
from src.db.database import Database
from src.utils.audio_utils import increase_speed
text_model = load_text_model(os.getenv("TEXT_MODEL_NAME"))
audio_model = load_audio_model(os.getenv("AUDIO_MODEL_NAME"))

def make_podcast(student_id, month):
    # CREATE TEMP FOLDERS
    os.makedirs(os.path.join(os.getenv("TEMP_AUDIO_DIR"),str(student_id)), exist_ok=True)
    os.makedirs(os.path.join(os.getenv("TEMP_IMAGE_DIR"),str(student_id)), exist_ok=True)
    os.makedirs(os.path.join(os.getenv("TEMP_VIDEO_DIR"),str(student_id)), exist_ok=True)

    script, highlight, improve = generate_script(student_id, month)
    print(improve)
    # CREATE AUDIO
    for key, value in script.items():
        audio_path = os.path.join(os.getenv("TEMP_AUDIO_DIR"), str(student_id), f"{key}.m4a")
        audio_model.generate_audio(value, audio_path)
        audio_path = increase_speed(audio_path, audio_path, 1.75)
        # CREATE VIDEO
        if key == "intro":
            class_name = get_class(student_id, month)
            class_name = class_name[0]["grade"] + "-" + "-".join(class_name[0]["level"].split("_"))

            image_path = os.path.join(os.getenv("INPUT_IMAGE_DIR"), "1.png")
            intro_image = add_information_to_intro_image(image = load_image(image_path), 
                                                         name = get_name(student_id, month)[0]["full_name"], 
                                                         class_name = class_name, 
                                                         teacher = get_teacher(student_id)[0]["care_specialist_fullname"], 
                                                         tutor = "ABC",
                                                         save_path = os.path.join(os.getenv("TEMP_IMAGE_DIR"), str(student_id), f"{key}.png")
                                                        )
            
            create_intro_part(audio_path, 
                              value, 
                              os.path.join(os.getenv("TEMP_VIDEO_DIR"), str(student_id), f"{key}.mp4"), 
                              os.path.join(os.getenv("TEMP_IMAGE_DIR"), str(student_id), f"{key}.png"))
        
        elif key == "highlight":
            create_highlight_part(
                audio_path,
                value,
                os.path.join(os.getenv("TEMP_VIDEO_DIR"), str(student_id), f"{key}.mp4"),
                os.path.join(os.getenv("INPUT_IMAGE_DIR"), "2.png"),
                highlight,
            )

        elif key in ["improve", "solution"]:
            create_improve_part(
                audio_path,
                value,
                os.path.join(os.getenv("TEMP_VIDEO_DIR"), str(student_id), f"{key}.mp4"),
                os.path.join(os.getenv("INPUT_IMAGE_DIR"), "3.png"),
                improve
            )
        
        elif key == "conclusion":
            create_final_part(audio_path, 
                              value, 
                              os.path.join(os.getenv("TEMP_VIDEO_DIR"), str(student_id), f"{key}.mp4"), 
                              [os.path.join(os.getenv("INPUT_IMAGE_DIR"), "4.png"), os.path.join(os.getenv("INPUT_IMAGE_DIR"), "5.png")]
                            )
        
    # COMBINE VIDEO
    video_paths = []
    for key in script.keys():
        video_paths.append(os.path.join(os.getenv("TEMP_VIDEO_DIR"), str(student_id), f"{key}.mp4"))
    
    out_video = os.path.join(os.getenv("OUTPUT_VIDEO_DIR", ""), f"{student_id}_{month}.mp4")
    combine_video(video_paths, out_video)

    add_background_music(
        out_video,
        os.path.join(os.getenv("INPUT_MUSIC_DIR", ""), "background.mp3"),
        out_video,
        music_volume=0.2,
        loop_music=True,
    )

def generate_script(student_id, month):
    highlight = convert_d2t(get_highlight(student_id, month))
    content = convert_d2t(get_content(student_id, month))   
    improve = convert_d2t(get_improve(student_id, month))
    name = get_name(student_id, month)[0]["full_name"]
    teacher = get_teacher(student_id)[0]["care_specialist_fullname"]

    # Generate content
    result = text_model.generate_script({
        "highlight": highlight,
        "others": content,
        "improve": improve,
        "month": month,
        "name": name,
        "teacher": teacher,
    })

    return result, highlight, improve

def check_add_music(video_path, music_path, output_path):
    add_background_music(video_path, music_path, output_path)