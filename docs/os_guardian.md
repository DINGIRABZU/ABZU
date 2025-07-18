# OS Guardian

The OS Guardian coordinates system automation under strict policy control. It consists of four building blocks:

1. **Perception** – captures the screen and detects interface elements using optional OpenCV and YOLO models.
2. **Action engine** – wraps `pyautogui`, shell commands and Selenium to perform mouse, keyboard and browser actions.
3. **Planning** – converts natural language instructions into ordered tool calls via a small LangChain agent and vector memory.
4. **Safety** – checks permissions for commands, domains and applications while tracking undo callbacks.

These modules can be invoked individually or through the ``os-guardian`` command line interface.
