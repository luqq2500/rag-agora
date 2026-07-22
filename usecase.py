import time

from infra.rag import RAGService

class AskRagAgoraUseCase:
    def __init__(self, rag_service: RAGService):
        self.service = rag_service

    def run(self):
        print(f"\nWelcome to AGORA AI Governance Chat Assistant!"
              f"\nPowered by HuggingFace MpNet-Base-v2 & Ollama Mini 3.5)\n")

        while True:
            request = input("Enter question ('quit' to exit): ")
            if request == "quit":
                print(f"Thank you for using AGORA AI Chat Assistant and see you again!")
                break

            print(f'\n🔍 Searching, 📜 retrieving documents, and 📝 preparing response...\n')
            start = time.time()
            self.service.run(request)
            end = time.time()
            print(f"\nFinished response in {end - start} seconds.\n")