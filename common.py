import os
import redis
from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
VK_BOT_TOKEN = os.getenv('VK_BOT_TOKEN')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 18571))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')



def log_info(msg):
    print(f"[INFO] {msg}")


def log_error(msg):
    print(f"[ERROR] {msg}")


def log_event(user_id, event):
    print(f"[EVENT] user:{user_id} -> {event}")


redis_client = None
if REDIS_HOST:
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        redis_client.ping()
        log_info("Redis connected")
    except Exception as e:
        log_error(f"Redis error: {e}")
        redis_client = None


def save_user_question(user_id, question_number):
    if redis_client:
        redis_client.set(f"user:{user_id}:question", question_number)
        log_event(user_id, f"question saved: {question_number}")


def get_user_question(user_id):
    if redis_client:
        return redis_client.get(f"user:{user_id}:question")
    return None


def save_user_score(user_id, score):
    if redis_client:
        redis_client.set(f"user:{user_id}:score", score)
        log_event(user_id, f"score updated: {score}")


def get_user_score(user_id):
    if redis_client:
        score = redis_client.get(f"user:{user_id}:score")
        return int(score) if score else 0
    return 0


def clear_user_question(user_id):
    if redis_client:
        redis_client.delete(f"user:{user_id}:question")
        log_event(user_id, "question cleared")


def parse_quiz_file(file_path):
    with open(file_path, "r", encoding="koi8-r") as f:
        text = f.read()

    questions = {}
    for block in text.split("Вопрос ")[1:]:
        if ":" in block and "Ответ:" in block:
            num, rest = block.split(":", 1)
            q_text, a_text = rest.split("Ответ:", 1)
            questions[num.strip()] = (q_text.strip(), a_text.strip())
    return questions


def load_all_quiz_questions():
    all_questions = {}
    if os.path.exists("quiz-questions"):
        count = 0
        for filename in os.listdir("quiz-questions"):
            if filename.endswith('.txt'):
                try:
                    questions = parse_quiz_file(f"quiz-questions/{filename}")
                    all_questions.update(questions)
                    count += len(questions)
                    log_info(f"Loaded {len(questions)} questions from {filename}")
                except Exception as e:
                    log_error(f"Error loading {filename}: {e}")
        log_info(f"Total questions loaded: {count}")
    else:
        log_error("Folder 'quiz-questions' not found")
    return all_questions