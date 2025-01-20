import time

class OutputManager:
    def __init__(self, debug: bool = False):
        """
        Initializes the OutputManager with an optional debug flag.

        Args:
            debug (bool): If True, includes timestamp and message level in logs.
        """
        self.logs = []
        self.debug = debug  # Determines whether to include debug information

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with optional timestamp and level, based on debug flag.

        Args:
            message (str): The message to log.
            level (str): The log level (e.g., INFO, ERROR).
        """
        if self.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            formatted_message = f"[{timestamp}] [{level}] {message}"
        else:
            formatted_message = message

        self.logs.append(formatted_message)
        print(formatted_message)  # Print in real-time

    def log_section(self, title: str, content: str):
        """
        Log a formatted section with a title and indented content.

        Args:
            title (str): The title of the section.
            content (str): The content to log, formatted with indents.
        """
        self.log(f"🔍 {title}:\n    {content.replace('\n', '\n    ')}")

    def log_with_emojis(self, title: str, details: dict):
        """
        Log structured details with emojis.

        Args:
            title (str): The title of the section.
            details (dict): A dictionary of key-value pairs to log.
        """
        self.log(f"✨ {title}:")
        for key, value in details.items():
            self.log(f"    {key}: {value}")

    def dump_logs(self):
        """
        Dump all logs for debugging.

        Returns:
            str: All logged messages joined by newlines.
        """
        return "\n".join(self.logs)
