import time

from infra.model import OllamaModel
from infra.vector_store import ChromaDB
from usecase.rag import AgoraRAGUseCase

if __name__ == "__main__":
    vector_store = ChromaDB()
    gen_model = OllamaModel()
    rag = AgoraRAGUseCase(vector_store, gen_model)

    print(f"\nWelcome to AGORA AI Governance Chat Assistant!"
          f"\nPowered by HuggingFace MpNet-Base-v2 & Ollama Mini 3.5)\n")

    is_running = True
    while is_running:
        request = input("Enter question ('quit' to exit): ")
        if request == "quit":
            is_running = False
            print(f"Thank you for using AGORA AI Chat Assistant and see you again!")
            break

        print(f'\n🔍 Searching, 📜 retrieving documents, and 📝 preparing response...\n')
        start = time.time()
        rag.run(request)
        end = time.time()
        print(f"\nFinished response in {end - start} seconds.\n")

