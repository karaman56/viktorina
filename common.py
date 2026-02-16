import os
import redis
from dotenv import load_dotenv


def init_redis_client(redis_host, redis_port, redis_password):
    client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3
    )
    client.ping()
    return client


def save_user_question(user_id, question_number, redis_client, platform='tg'):
    if redis_client:
        key = f"{platform}:user:{user_id}:question"
        redis_client.set(key, question_number)


def get_user_question(user_id, redis_client, platform='tg'):
    if redis_client:
        key = f"{platform}:user:{user_id}:question"
        return redis_client.get(key)
    return None


def save_user_score(user_id, score, redis_client, platform='tg'):
    if redis_client:
        key = f"{platform}:user:{user_id}:score"
        redis_client.set(key, score)


def get_user_score(user_id, redis_client, platform='tg'):
    if redis_client:
        key = f"{platform}:user:{user_id}:score"
        score = redis_client.get(key)
        return int(score) if score else 0
    return 0


def clear_user_question(user_id, redis_client, platform='tg'):
    if redis_client:
        key = f"{platform}:user:{user_id}:question"
        redis_client.delete(key)


def parse_quiz_file(file_path):
    with open(file_path, "r", encoding="koi8-r") as f:
        text = f.read()
    questions = {}
    for block in text.split("Вопрос ")[1:]:
        try:
            if ":" not in block or "Ответ:" not in block:
                continue
            question_number, remaining = block.split(":", 1)
            question_text, answer_text = remaining.split("Ответ:", 1)
            questions[question_number.strip()] = (question_text.strip(), answer_text.strip())
        except ValueError:
            continue
    return questions


def load_all_quiz_questions(questions_path):
    questions = {}
    questions_path = os.path.abspath(questions_path)

    if os.path.exists(questions_path):
        for filename in os.listdir(questions_path):
            if filename.endswith('.txt'):
                try:
                    parsed_questions = parse_quiz_file(os.path.join(questions_path, filename))
                    questions.update(parsed_questions)
                except (OSError, UnicodeDecodeError) as error:
                    print(f"⚠️ Ошибка загрузки {filename}: {error}")
    return questions


def main():
    load_dotenv()
    quiz_questions_path = os.getenv('QUIZ_QUESTIONS_PATH', 'quiz-questions')
    redis_client = None
    if os.getenv('REDIS_HOST'):
        try:
            redis_client = init_redis_client(
                os.getenv('REDIS_HOST'),
                int(os.getenv('REDIS_PORT', 18571)),
                os.getenv('REDIS_PASSWORD')
            )
            print("✅ Redis connected")
        except redis.ConnectionError:
            print("❌ Redis connection failed")
        except redis.TimeoutError:
            print("❌ Redis timeout")
        except ValueError:
            print("❌ Invalid Redis port")


if __name__ == '__main__':
    main()