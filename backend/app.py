import gzip
from flask import Flask, jsonify, request
from flask_cors import CORS
from groq import Groq
import json
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# =====================================
# 1. PROJECT SETTINGS
# =====================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "cars.json.gz"
ENV_FILE = BASE_DIR / ".env"


# =====================================
# 2. LOAD API KEY
# =====================================

if ENV_FILE.exists():
    with open(ENV_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)

                os.environ.setdefault(
                    key.strip(),
                    value.strip().strip('"').strip("'")
                )


# =====================================
# 3. LOAD CAR DATASET
# =====================================

with gzip.open(DATA_FILE, "rt", encoding="utf-8") as file:
    cars_data = json.load(file)


# =====================================
# 4. HOME
# =====================================

@app.route("/")
def home():
    return jsonify({
        "message": "ELITE MOTORS API is running!"
    })


# =====================================
# 5. GET ALL COMPANIES
# =====================================

@app.route("/api/companies")
def get_companies():

    companies = [
        company["brand"]
        for company in cars_data
        if company.get("brand")
    ]

    return jsonify({
        "total": len(companies),
        "companies": companies
    })


# =====================================
# 6. GET DATASET INFORMATION
# =====================================

@app.route("/api/cars")
def get_cars():

    return jsonify({
        "total_companies": len(cars_data),
        "message": "Car dataset loaded successfully"
    })


# =====================================
# 7. GET CARS BY BRAND
# =====================================

@app.route("/api/cars/<brand>")
def get_cars_by_brand(brand):

    for company in cars_data:

        if company.get("brand", "").lower() == brand.lower():

            return jsonify({
                "brand": company["brand"],
                "data": company["data"]
            })

    return jsonify({
        "error": "Brand not found"
    }), 404


# =====================================
# 8. EXTRACT MAKES
# =====================================

def extract_makes(company):

    data = company.get("data", {})

    if isinstance(data, dict):
        return data.get("makes", [])

    if isinstance(data, list):
        return data

    return []


# =====================================
# 9. FEATURED CARS
# =====================================

@app.route("/api/featured-cars")
def get_featured_cars():

    candidates = []

    for company_index, company in enumerate(cars_data):

        brand = company.get("brand", "")
        makes = extract_makes(company)

        best_car = None
        best_score = -1

        for make_index, make in enumerate(makes):

            if not isinstance(make, dict):
                continue

            models = make.get("models", [])

            for model_index, model in enumerate(models):

                if not isinstance(model, dict):
                    continue

                model_name = model.get("name", "").strip()

                if not model_name or model_name == ".":
                    continue

                generations = model.get("generations", [])

                for generation_index, generation in enumerate(generations):

                    if not isinstance(generation, dict):
                        continue

                    engines = generation.get("engines", [])
                    engine = engines[0] if engines else {}

                    if not isinstance(engine, dict):
                        engine = {}

                    year = generation.get("yearStart")

                    score = sum([
                        year is not None,
                        engine.get("label") is not None,
                        engine.get("powerHp") is not None,
                        engine.get("torqueNm") is not None,
                        engine.get("fuelType") is not None,
                        engine.get("transmission") is not None
                    ])

                    if score > best_score:

                        best_score = score

                        best_car = {
                            "id": f"{company_index}-{make_index}-{model_index}-{generation_index}",
                            "brand": brand,
                            "model": model_name,
                            "displayName": f"{brand.replace('-', ' ').title()} {model_name}",
                            "searchKey": f"{brand}|{model_name}",
                            "year": year,
                            "engine": engine.get("label"),
                            "powerHp": engine.get("powerHp"),
                            "torqueNm": engine.get("torqueNm"),
                            "fuelType": engine.get("fuelType"),
                            "transmission": engine.get("transmission")
                        }

        if best_car and best_score >= 3:
            candidates.append(best_car)

    candidates.sort(
        key=lambda car: (
            car["year"] or 0,
            car["powerHp"] or 0
        ),
        reverse=True
    )

    selected_cars = candidates[:20]

    return jsonify({
        "total": len(selected_cars),
        "cars": selected_cars
    })


# =====================================
# 10. FIND CAR IN DATASET
# =====================================

def find_car(search_key):

    if not search_key or "|" not in search_key:
        return None

    brand, model_name = search_key.split("|", 1)

    for company in cars_data:

        if company.get("brand", "").lower() != brand.lower():
            continue

        for make in extract_makes(company):

            if not isinstance(make, dict):
                continue

            for model in make.get("models", []):

                if not isinstance(model, dict):
                    continue

                if model.get("name", "").lower() == model_name.lower():

                    return {
                        "brand": company.get("brand"),
                        "model": model.get("name"),
                        "generations": model.get("generations", [])
                    }

    return None


# =====================================
# 11. FIND CAR FROM CUSTOMER MESSAGE
# =====================================

def find_car_from_message(message):

    message_lower = message.lower().replace("-", " ")
    matches = []

    for company in cars_data:

        brand = company.get("brand", "")
        brand_normalized = brand.lower().replace("-", " ")

        if not brand_normalized:
            continue

        makes = extract_makes(company)

        for make in makes:

            if not isinstance(make, dict):
                continue

            for model in make.get("models", []):

                if not isinstance(model, dict):
                    continue

                model_name = model.get("name", "")
                model_normalized = model_name.lower().replace("-", " ")

                if not model_normalized:
                    continue

                if (
                    brand_normalized in message_lower
                    and model_normalized in message_lower
                ):
                    matches.append({
                        "brand": brand,
                        "model": model_name,
                        "generations": model.get("generations", [])
                    })

    if not matches:
        return None

    return max(
        matches,
        key=lambda car: len(car["brand"]) + len(car["model"])
    )


# =====================================
# 12. PREPARE SMALL CAR INFORMATION
# =====================================

def prepare_car_information(car):

    compact_car = {
        "brand": car["brand"],
        "model": car["model"],
        "generations": []
    }

    generations = car.get("generations", [])

    # آخر 3 أجيال فقط
    for generation in generations[-3:]:

        if not isinstance(generation, dict):
            continue

        compact_generation = {
            "yearStart": generation.get("yearStart"),
            "yearEnd": generation.get("yearEnd"),
            "engines": []
        }

        engines = generation.get("engines", [])

        # أول 5 محركات فقط
        for engine in engines[:5]:

            if not isinstance(engine, dict):
                continue

            engine_info = {}

            important_fields = [
                "label",
                "powerHp",
                "torqueNm",
                "fuelType",
                "transmission"
            ]

            for key in important_fields:

                if engine.get(key) is not None:
                    engine_info[key] = engine[key]

            compact_generation["engines"].append(engine_info)

        compact_car["generations"].append(compact_generation)

    return json.dumps(
        compact_car,
        ensure_ascii=False
    )


# =====================================
# 13. AI CHATBOT - GROQ
# =====================================

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    search_key = data.get("searchKey") or ""
    message = data.get("message") or ""
    history = data.get("history") or []

    if not isinstance(message, str):
        return jsonify({"error": "Invalid message"}), 400

    message = message.strip()

    if not message:
        return jsonify({
            "error": "Please enter a message"
        }), 400

    # 1. Find a car selected by the customer
    car = find_car(search_key) if search_key else None

    # 2. Find a car mentioned in the current question
    if not car:
        car = find_car_from_message(message)

    # 3. If no car was mentioned now, look at recent conversation
    if not car and isinstance(history, list):

        for old_message in reversed(history):

            if not isinstance(old_message, dict):
                continue

            old_text = old_message.get(
                "content",
                old_message.get("text", "")
            )

            if old_text:
                car = find_car_from_message(str(old_text))

                if car:
                    break

    # 4. Prepare car data only when a car was identified
    if car:
        car_information = prepare_car_information(car)
        current_car = f'{car["brand"]} {car["model"]}'
    else:
        car_information = (
            "No specific car was identified in the current question. "
            "Do not invent car specifications."
        )
        current_car = "No specific car selected."

    # 5. Check API Key
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return jsonify({
            "error": "Groq API key is missing"
        }), 500

    try:

        client = Groq(api_key=api_key)

        # 6. System instructions
        ai_messages = [
            {
                "role": "system",

                "content": f"""
You are ELITE AI, the official intelligent car assistant
of ELITE MOTORS.

CURRENT CAR:
{current_car}

CAR DATABASE:
{car_information}

ROLE AND SCOPE:
- You are a friendly, intelligent and professional car consultant.
- Your main specialization is cars and ELITE MOTORS.
- You can answer greetings and general car-related questions
  even when no specific car has been selected.
- Explain car terminology and help customers understand vehicles.
- Help customers choose a car based on their stated needs.
- If a question is unrelated to cars, politely guide the conversation
  back to cars and ELITE MOTORS.

LANGUAGE:
- Understand Egyptian Arabic, Modern Standard Arabic and English.
- Reply in the same language used by the customer.
- Use natural Egyptian Arabic when the customer speaks Egyptian Arabic.

CAR FACTS AND ACCURACY:
- Use only the provided database for specific vehicle facts.
- Never invent prices, horsepower, engine details, features,
  availability or specifications.
- If a requested detail is missing, say it is unavailable
  in the database.
- Do not confuse different generations or engine variants.
- Do not claim a vehicle is in stock unless stock information
  is explicitly provided.
- Clearly distinguish database facts from general advice.
- If the customer asks about a car not found in the database,
  explain that its details are not currently available.

CONVERSATION:
- Use the conversation history to understand follow-up questions.
- Understand expressions such as "it", "this car", "هي", "دي",
  "بتاعتها" and "سرعتها".
- Do not ask the customer to repeat information already provided.
- If the customer mentions a different car, use the newly mentioned car.
- If the intended car is unclear, ask one short clarification question.

ANSWER FORMAT:
- Use clear headings when useful.
- Use bullet points for specifications.
- Use tables for comparisons when useful.
- Keep answers readable and appropriately concise.
- Explain technical terms simply.
- Be honest, helpful and professional.
"""
            }
        ]

        # 7. Add only the latest six conversation messages
        if isinstance(history, list):

            for old_message in history[-6:]:

                if not isinstance(old_message, dict):
                    continue

                role = old_message.get("role")

                content = old_message.get(
                    "content",
                    old_message.get("text", "")
                )

                if (
                    role in ["user", "assistant"]
                    and isinstance(content, str)
                    and content.strip()
                ):
                    ai_messages.append({
                        "role": role,
                        "content": content[:1200]
                    })

        # 8. Add the current question
        ai_messages.append({
            "role": "user",
            "content": message
        })

        # 9. Send request to Groq
        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=ai_messages,

            temperature=0.4,

            max_tokens=900

        )

        answer = response.choices[0].message.content

        if not answer:
            raise RuntimeError("AI returned an empty response")

        # 10. Return the answer
        return jsonify({

            "answer": answer,

            "car": current_car

        })

    except Exception:

        app.logger.exception("Groq API request failed")

        return jsonify({
            "error": "AI service error. Please try again."
        }), 502


# =====================================
# 14. RUN SERVER
# =====================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )