import time

from core.service import AgoraResearchAssistantService

class ChatAgoraResearchAssistant:
    def __init__(self, service: AgoraResearchAssistantService):
        self.service = service

    def run(self):
        print(f"\nWelcome to AGORA AI Governance Chat Assistant!")
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