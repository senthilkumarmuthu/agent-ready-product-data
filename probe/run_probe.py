#!/usr/bin/env python3
"""LLM probe for the product-data readiness study (H5).

Sends each probe item to a local Ollama model and saves the answers.
Standard library only. Safe to stop and restart: finished items are skipped.

Usage:  python3 run_probe.py llama3.2:3b
        python3 run_probe.py qwen2.5:3b
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = "http://localhost:11434"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "llama3.2:3b"
OUT = os.path.join(HERE, "answers_" + MODEL.replace(":", "_").replace("/", "_") + ".jsonl")
OPTIONS = {"temperature": 0, "seed": 20261120, "num_ctx": 4096, "num_predict": 256}

SYSTEM = ("You are a shopping assistant. Answer only from the product data you are given. "
          "If the data does not state the answer, use null. Reply in JSON.")
SCHEMA = {
    "price": {"type": "object", "properties": {"price": {"type": ["number", "null"]}, "currency": {"type": ["string", "null"]}},
              "required": ["price", "currency"]},
    "stock": {"type": "object", "properties": {"in_stock_today": {"type": ["boolean", "null"]}}, "required": ["in_stock_today"]},
    "id": {"type": "object", "properties": {"gtin": {"type": ["string", "null"]}, "mpn": {"type": ["string", "null"]}},
           "required": ["gtin", "mpn"]},
}


def call(path, body=None, timeout=600):
    req = urllib.request.Request(OLLAMA + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def main():
    try:
        tags = call("/api/tags")
    except Exception as e:
        sys.exit(f"Can't reach Ollama at {OLLAMA}. Is the Ollama app running? ({e})")
    digest = next((m.get("digest") for m in tags.get("models", []) if m.get("name") == MODEL), None)
    if not digest:
        sys.exit(f"Model {MODEL} isn't downloaded. Run: ollama pull {MODEL}")

    items = [json.loads(l) for l in open(os.path.join(HERE, "probe_items.jsonl"))]
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
    todo = [it for it in items if it["id"] not in done]
    print(f"{MODEL} ({digest[:12]}): {len(done)} done, {len(todo)} to go", flush=True)

    t0 = time.time()
    with open(OUT, "a") as out:
        for i, it in enumerate(todo, 1):
            body = {"model": MODEL, "stream": False, "format": SCHEMA[it["q"]], "options": OPTIONS,
                    "messages": [{"role": "system", "content": SYSTEM},
                                 {"role": "user", "content": f"Product data (JSON-LD):\n{it['jsonld']}\n\nQuestion: {it['question']}"}]}
            for attempt in range(3):
                try:
                    r = call("/api/chat", body)
                    break
                except Exception as e:
                    if attempt == 2:
                        sys.exit(f"Stopped at {it['id']} after 3 tries: {e}. Run the same command again to resume.")
                    time.sleep(5)
            out.write(json.dumps({"id": it["id"], "model": MODEL, "digest": digest, "options": OPTIONS,
                                  "raw": r.get("message", {}).get("content", "")}, ensure_ascii=False) + "\n")
            out.flush()
            if i % 50 == 0 or i == len(todo):
                rate = (time.time() - t0) / i
                print(f"  {len(done) + i}/{len(items)}  about {rate * (len(todo) - i) / 60:.0f} min left", flush=True)
    print(f"Finished. Answers saved to {OUT}")


if __name__ == "__main__":
    main()
