# Nautilus MetaTrader 5 Adapter 🌟

This adapter allows for seamless integration between the Nautilus Trader and MetaTrader 5, providing capabilities for market data retrieval, order execution, and account management through the MetaTrader 5 Terminal using either IPC for Windows, RPyC for Linux, or Sockets for EA (suitable for streaming).

## Client Modes 🛠️

This extension supports two different client modes:

1. **IPC Mode** (Using the MetaTrader Python library) 📦
   - Directly communicates with MetaTrader 5 via the official Python API which uses `IPC` (Inter-Process Communication).
   - Best for local integration without additional network overhead but does not support real-time updates.

   *For Linux systems* 🐧
   - Uses `RPyC` (Remote Python Call) to bridge between a Linux environment and MT5 running inside Wine, it uses `IPC` under the hood.
   - Ideal for automated trading setups on non-Windows environments.

2. **Socket Mode** (Using MetaTrader EA) 🌐
   - Connects to the MetaTrader 5 Expert Advisor (EA) via a custom socket server.
   - Enables external programs (Python, JavaScript, C++) to interact with MT5.
   - Supports real-time updates.

## Installation ⚙️

To install the MetaTrader 5 Adapter, follow these steps:

1. Clone the repository:
   ```sh
   git clone https://github.com/quantspub/nautilus_mt5.git
   ```

2. Navigate to the project directory:
   ```sh
   cd /nautilus_mt5
   ```

3. Pull the Docker image:
   ```sh
   docker pull docker.io/quantspub/metatrader5-terminal:latest
   ```

4. Install the required Python packages:
   ```sh
   poetry install
   ```

## Usage 🖥️

To run the MetaTrader 5 Adapter, execute the following commands:

```bash
cd examples
```

```bash
cp .env.example .env
```

```bash
python connect_with_dockerized_terminal.py
```

**NOTE:** Make sure to configure the `.env` file properly before running the script or the Docker image. ⚠️

### Detailed Steps:

1. Ensure Docker is installed and running on your machine.
2. Clone the repository and navigate to the project directory.
3. Pull the Docker image for MetaTrader 5 Terminal.
4. Install the required Python packages using Poetry.
5. Navigate to the `examples` directory.
6. Copy the `.env.example` file to `.env` and configure it with your MetaTrader 5 credentials.
7. Run the `connect_with_dockerized_terminal.py` script to start the adapter.

## Project Structure 🗂️

The project structure is organized as follows:

```
nautilus_mt5/
├── examples/
│   ├── connect_with_dockerized_terminal.py
│   ├── .env.example
│   └── ...
├── nautilus_mt5/    # Source code for the adapter
├── tests/                   # Test cases
├── MQL5/                    # MQL5 scripts and EA module
├── docs/                    # Documentation files
├── pyproject.toml           # Poetry configuration
├── poetry.lock              # Dependency lock file
├── build.py                 # Build script
├── .gitignore               # Git ignore file
├── LICENSE                  # License file
├── README.md                # Project documentation
```

## Contributing 🤝

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes. 🐛

1. Fork the repository. 🍴
2. Create a new branch:
   ```sh
   git checkout -b feature-branch
   ```
3. Make your changes. ✏️
4. Commit your changes:
   ```sh
   git commit -m 'Add some feature'
   ```
5. Push to the branch:
   ```sh
   git push origin feature-branch
   ```
6. Open a pull request. 📥

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Credits 🙏

- [PyTrader Python MT4/MT5 Trading API Connector](https://github.com/TheSnowGuru/PyTrader-python-mt4-mt5-trading-api-connector-drag-n-drop) 🌟
- [MQL5 Articles](https://www.mql5.com/en/articles/234) 📚
- [MQL5 Forum](https://www.mql5.com/en/forum/244840) 💬

## Support 📞

If you encounter any issues or have questions, feel free to open an issue on the GitHub repository or contact the author via email at [quantspub@gmail.com](mailto:quantspub@gmail.com)

