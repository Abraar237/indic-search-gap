"""Open-weight arm: serve Qwen3-30B-A3B-Instruct-2507 (FP8) with vLLM on Modal as an OpenAI-compatible
endpoint with tool calling (hermes parser). Deploy:

    python3 -m modal deploy experiments/modal_vllm.py
    # prints a URL like https://<workspace>--indic-vllm-serve.modal.run ; put it in .env as MODAL_VLLM_URL

The runner then uses model id "modal/Qwen3-30B-A3B-Instruct-2507" and agent.post routes to this URL.
GPU time is the cost (A100-40GB); there is no usage.cost, so the runner logs GPU seconds instead
(results/spend_modal.json). Scale to zero after 5 idle minutes so an idle deploy costs nothing.
"""
import modal

MODEL = "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
SERVED = "Qwen3-30B-A3B-Instruct-2507"
PORT = 8000

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.11.0", "transformers==4.57.1", "huggingface_hub[hf_transfer]")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "VLLM_USE_V1": "1"})
)
vol = modal.Volume.from_name("indic-hf-cache", create_if_missing=True)
app = modal.App("indic-vllm")


@app.function(
    image=image,
    gpu="A100-40GB",
    scaledown_window=300,
    timeout=60 * 60,
    volumes={"/root/.cache/huggingface": vol},
)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=15 * 60)
def serve():
    import subprocess
    cmd = [
        "vllm", "serve", MODEL, "--served-model-name", SERVED, "--host", "0.0.0.0", "--port", str(PORT),
        "--max-model-len", "16384", "--gpu-memory-utilization", "0.92",
        "--enable-auto-tool-choice", "--tool-call-parser", "hermes",
        "--enable-prefix-caching", "--disable-log-requests",
    ]
    subprocess.Popen(" ".join(cmd), shell=True)
