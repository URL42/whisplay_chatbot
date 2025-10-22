import { exec } from "child_process";
import { resolve } from "path";
import { Socket } from "net";
import { getCurrentTimeTag, splitSentences } from "../utils";

interface Status {
  status: string;
  emoji: string;
  text: string;
  scroll_speed: number;
  brightness: number;
  RGB: string;
  battery_color: string;
  battery_level: number;
}

const MAX_CHARACTERS = 25 * 6; // 25 characters per line, 6 lines

const autoCropText = (text: string): string => {
  return text;
  // if (text.length <= MAX_CHARACTERS) {
  //   return text;
  // }
  // const { sentences, remaining } = splitSentences(text);
  // while (sentences.join(" ").length > MAX_CHARACTERS && sentences.length > 0) {
  //   sentences.shift();
  // }
  // return sentences.join(" ") + remaining;
};

export class WhisplayDisplay {
  private currentStatus: Status = {
    status: "starting",
    emoji: "😊",
    text: "",
    scroll_speed: 3,
    brightness: 100,
    RGB: "#00FF30",
    battery_color: "#000000",
    battery_level: 100, // 0-100
  };

  private client = null as Socket | null;
  private buttonPressedCallback: () => void = () => {};
  private buttonReleasedCallback: () => void = () => {};
  private isReady: Promise<void>;
  private pythonProcess: any; // Placeholder for Python process if needed

  

  constructor() {
    this.startPythonProcess();
    this.isReady = new Promise<void>((resolve) => {
      this.connectWithRetry(15, resolve);
    });
  }

  startPythonProcess(): void {
    const command = `cd ${resolve(
      __dirname,
      "../../python"
    )} && python3 chatbot-ui.py`;
    console.log("Starting Python process...");
    this.pythonProcess = exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error("Error starting Python process:", error);
        return;
      }
      console.log("Python process stdout:", stdout);
      console.error("Python process stderr:", stderr);
    });
    this.pythonProcess.stdout.on("data", (data: any) =>
      console.log(data.toString())
    );
    this.pythonProcess.stderr.on("data", (data: any) =>
      console.error(data.toString())
    );
  }

  killPythonProcess(): void {
    if (this.pythonProcess) {
      console.log("Killing Python process...");
      this.pythonProcess.kill();
      this.pythonProcess = null;
    }
  }

  async connectWithRetry(
    retries: number = 10,
    outerResolve: () => void
  ): Promise<void> {
    await new Promise((resolve, reject) => {
      const attemptConnection = (attempt: number) => {
        this.connect()
          .then(() => {
            resolve(true);
          })
          .catch((err) => {
            if (attempt < retries) {
              console.log(`Connection attempt ${attempt} failed, retrying...`);
              setTimeout(() => attemptConnection(attempt + 1), 5000);
            } else {
              console.error("Failed to connect after multiple attempts:", err);
              reject(err);
            }
          });
      };
      attemptConnection(1);
    });
    outerResolve();
  }

  async connect(): Promise<void> {
    console.log("Connecting to local display socket...");
    return new Promise<void>((resolve, reject) => {
      // 销毁原来的this.client
      if (this.client) {
        this.client.destroy();
      }
      this.client = new Socket();
      this.client.connect(12345, "0.0.0.0", () => {
        console.log("Connected to local display socket");
        this.sendToDisplay(JSON.stringify(this.currentStatus));
        resolve();
      });
      this.client.on("data", (data: Buffer) => {
        const dataString = data.toString();
        console.log(
          `[${getCurrentTimeTag()}] Received data from Whisplay hat:`,
          dataString
        );
        if (dataString.trim() === "OK") {
          return;
        }
        try {
          const json = JSON.parse(dataString);
          if (json.event === "button_pressed") {
            this.buttonPressedCallback();
          }
          if (json.event === "button_released") {
            this.buttonReleasedCallback();
          }
        } catch {
          console.error("Failed to parse JSON from data");
        }
      });
      this.client.on("error", (err: any) => {
        console.error("Socket error:", err);
        // 如果是ECONNREFUSED
        if (err.code === "ECONNREFUSED") {
          reject(err);
        }
      });
    });
  }

  onButtonPressed(callback: () => void): void {
    this.buttonPressedCallback = callback;
  }

  onButtonReleased(callback: () => void): void {
    this.buttonReleasedCallback = callback;
  }

  private async sendToDisplay(data: string): Promise<void> {
    await this.isReady;
    try {
      this.client?.write(`${data}\n`, "utf8", () => {
        // console.log("send", data);
      });
    } catch (error) {
      console.error("Failed to update display.");
    }
  }

  getCurrentStatus(): Status {
    return this.currentStatus;
  }

  async display(newStatus: Partial<Status> = {}): Promise<void> {
    if (newStatus.text) {
      newStatus.text = autoCropText(newStatus.text);
    }
    const {
      status,
      emoji,
      text,
      RGB,
      brightness,
      battery_level,
      battery_color,
    } = {
      ...this.currentStatus,
      ...newStatus,
    };

    const changedValues = Object.entries(newStatus).filter(
      ([key, value]) => (this.currentStatus as any)[key] !== value
    );

    const isTextChanged = changedValues.some(([key]) => key === "text");

    this.currentStatus.status = status;
    this.currentStatus.emoji = emoji;
    this.currentStatus.text = text;
    this.currentStatus.RGB = RGB;
    this.currentStatus.brightness = brightness;
    this.currentStatus.battery_level = battery_level;
    this.currentStatus.battery_color = battery_color;

    const changedValuesObj = Object.fromEntries(changedValues);
    changedValuesObj.brightness = 100;
    const data = JSON.stringify(changedValuesObj);
    if (isTextChanged) console.log("send data:", data);
    this.sendToDisplay(data);
  }
}

// Create a singleton instance to maintain backward compatibility
const displayInstance = new WhisplayDisplay();

export const display = displayInstance.display.bind(displayInstance);
export const getCurrentStatus =
  displayInstance.getCurrentStatus.bind(displayInstance);
export const onButtonPressed =
  displayInstance.onButtonPressed.bind(displayInstance);
export const onButtonReleased =
  displayInstance.onButtonReleased.bind(displayInstance);

// kill the Python process on exit signals
process.on("SIGINT", () => {
  console.log("SIGINT received, killing Python process...");
  displayInstance.killPythonProcess();
  process.exit(0);
});
process.on("SIGTERM", () => {
  console.log("SIGTERM received, killing Python process...");
  displayInstance.killPythonProcess();
  process.exit(0);
});
process.on("uncaughtException", (err) => {
  console.error("Uncaught Exception:", err);
  displayInstance.killPythonProcess();
});
process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  displayInstance.killPythonProcess();
});
process.on("keyboardInterrupt", () => {
  console.log("Keyboard Interrupt received, killing Python process...");
  displayInstance.killPythonProcess();
  process.exit(0);
});
