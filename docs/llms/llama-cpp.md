# llama.cpp setup

README: https://github.com/ggml-org/llama.cpp

Download: `brew install llama.cpp`

Install a model such as mistral:

```bash
# Download and run a model from Hugging Face
> llama-cli -hf ggml-org/gemma-3-1b-it-GGUF

# OpenAI-compatible server
> llama-server -hf ggml-org/gemma-3-1b-it-GGUF
```
