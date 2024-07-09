import time
from typing import Optional

class CanSend:
    """
    A class to implement rate limiting for sending messages.
    
    This class ensures that messages are not sent too frequently by
    enforcing a minimum time interval between sends.
    """

    def __init__(self, interval: float = 5.0):
        """
        Initialize the CanSend instance.

        Args:
            interval (float): The minimum time interval (in seconds) between sends.
                              Defaults to 5.0 seconds.
        """
        self.interval: float = interval
        self.last_send_time: Optional[float] = None

    def can_send(self) -> bool:
        """
        Check if enough time has passed to allow another send.

        Returns:
            bool: True if sending is allowed, False otherwise.
        """
        current_time = time.time()
        
        if self.last_send_time is None:
            self.last_send_time = current_time
            return True

        elapsed_time = current_time - self.last_send_time

        if elapsed_time >= self.interval:
            self.last_send_time = current_time
            return True
        else:
            return False

    def time_until_next_send(self) -> float:
        """
        Calculate the time remaining until the next send is allowed.

        Returns:
            float: The number of seconds until the next send is allowed.
                   Returns 0 if sending is currently allowed.
        """
        if self.last_send_time is None:
            return 0

        current_time = time.time()
        elapsed_time = current_time - self.last_send_time
        remaining_time = max(0, self.interval - elapsed_time)

        return remaining_time

    def reset(self) -> None:
        """
        Reset the last send time to allow immediate sending.
        """
        self.last_send_time = None
