import time


class OutputManager:
    def __init__(self, debug: bool = False):
        """
        Initializes the OutputManager.

        Args:
            debug (bool): If True, includes timestamp and message level in logs.
        """
        self.logs = []
        self.debug = debug  # Enables detailed logs

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with optional timestamp and level.

        Args:
            message (str): The message to log.
            level (str): The log level (e.g., INFO, ERROR).
        """
        if self.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            formatted_message = f"[{timestamp}] [{level}] {message}"
        else:
            formatted_message = message

        # Store in logs
        self.logs.append(formatted_message)

        # Output to console
        self._log_to_console(formatted_message)

    def log_section(self, title: str, content: str):
        """
        Log a formatted section with a title and indented content.

        Args:
            title (str): The title of the section.
            content (str): The content to log, formatted with indents.
        """
        indented_content = content.replace('\n', '\n    ')
        self.log(f"🔍 {title}:\n    {indented_content}")

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

    def dump_logs(self) -> str:
        """
        Dump all logs for debugging.

        Returns:
            str: All logged messages joined by newlines.
        """
        return "\n".join(self.logs)

    def _log_to_console(self, message: str):
        """
        Log a message to the console.

        Args:
            message (str): The message to log.
        """
        print(message)
