import time


class CanSend:
    def can_send(self):
        if not hasattr(self, "last_send_time"):
            self.last_send_time = time.time() - 20
        current_time = time.time()
        elapsed_time = current_time - self.last_send_time

        if elapsed_time >= 5:
            self.last_send_time = current_time
            return True
        else:
            return False
