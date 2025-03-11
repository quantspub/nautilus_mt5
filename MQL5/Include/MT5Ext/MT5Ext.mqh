//+------------------------------------------------------------------+
//|                                            MT5Ext.mqh            |
//+------------------------------------------------------------------+
#property copyright "QuantsPub"
#property version "0.1"

#include <MT5Ext\socket-library-mt4-mt5.mqh>
#include <MT5Ext\rest-handlers.mqh>
#include <MT5Ext\stream-handlers.mqh>
#include <MT5Ext\utils.mqh>

ServerSocket *restServer;
ServerSocket *streamingServer;
ClientSocket *streamingClients[];  // Store connected clients for streaming

// Create a new server socket for REST and streaming servers
void StartServers(ushort restPort, ushort streamPort, bool ForLocalhostOnly = true)
{
    restServer = new ServerSocket(restPort, ForLocalhostOnly);
    if (!restServer.Created())
    {
        Print("Failed to create REST server socket on port ", restPort);
    }
    else
    {
        Print("MQL5 REST server started on port ", restPort);
    }

    streamingServer = new ServerSocket(streamPort, true);
    if (!streamingServer.Created())
    {
        Print("Failed to create streaming server socket on port ", streamPort);
    }
    else
    {
        Print("MQL5 streaming server started on port ", streamPort);
    }
}

// Close and delete the server sockets
void CloseServers()
{
    if (restServer != NULL)
    {
        delete restServer;
        restServer = NULL;
    }

    if (streamingServer != NULL)
    {
        delete streamingServer;
        streamingServer = NULL;
    }

    for (int i = 0; i < ArraySize(streamingClients); i++)
    {
        if (streamingClients[i] != NULL)
        {
            delete streamingClients[i];
            streamingClients[i] = NULL;
        }
    }
}

void AcceptClients(bool onlyStream, bool debug)
{
    if (restServer != NULL)
    {
        ClientSocket *client = restServer.Accept();
        if (client != NULL && client.IsSocketConnected())
        {
            Print("New REST client connected: ", client);
            Print("Processing client request...");
            ProcessClient(*client, onlyStream, debug); 
            delete client;
        }
    }

    if (streamingServer != NULL)
    {
        ClientSocket *newClient = streamingServer.Accept();
        if (newClient != NULL && newClient.IsSocketConnected())
        {
            Print("New streaming client connected: ", newClient);
            ArrayResize(streamingClients, ArraySize(streamingClients) + 1);
            streamingClients[ArraySize(streamingClients) - 1] = newClient;
        }
    }
}

void ProcessClient(ClientSocket &client, bool onlyStream, bool debug = false)
{
    uchar buffer[4098];
    int received = client.Receive(buffer);

    if (received > 0)
    {
        if (debug)
        {
            Print("Received ", received, " bytes from client: ", &client);
        }

        string request = CharArrayToString(buffer, 0, received);
        if (debug)
        {
            Print("Received request: " + request);
        }

        string command, subCommand;
        string parameters[];
        ParseRequest(request, command, subCommand, parameters, debug);

        string response;
        if (command == "F000" && subCommand == "1")
        {
            response = GetCheckConnection();
        }
        else if (command == "F001" && subCommand == "1")
        {
            response = GetStaticAccountInfo();
        }
        else if (command == "F002" && subCommand == "1")
        {
            response = GetDynamicAccountInfo();
        }
        else if (command == "F003" && subCommand == "2")
        {
            response = GetInstrumentInfo(parameters[0]);
        }
        else if (command == "F007" && subCommand == "1")
        {
            response = GetBrokerInstrumentNames();
        }
        else if (command == "F004" && subCommand == "2")
        {
            response = CheckMarketWatch(parameters[0]);
        }
        else if (command == "F008" && subCommand == "2")
        {
            response = CheckTradingAllowed(parameters[0]);
        }
        else if (command == "F011" && subCommand == "1")
        {
            response = CheckTerminalServerConnection();
        }
        else if (command == "F012" && subCommand == "1")
        {
            response = CheckTerminalType();
        }
        else if (command == "F020" && subCommand == "2")
        {
            response = GetLastTickInfo(parameters[0]);
        }
        else if (command == "F005" && subCommand == "1")
        {
            response = GetBrokerServerTime();
        }
        else
        {
            string unknownRequest[] = {"UNKNOWN_REQUEST"};
            response = MakeMessage("F999", "1", unknownRequest);
        }

        if (onlyStream)
        {
            BroadcastStreamData(response);
        }
        else
        {
            client.Send(response);
        }
    }
}

void ParseRequest(const string &request, string &command, string &subCommand, string &parameters[], bool debug = false)
{
    // Split the request into command, sub_command, and parameters
    string parts[];
    StringSplit(request, '^', parts);

    if (ArraySize(parts) < 2)
    {
        command = "F999";
        subCommand = "1";
        parameters[0] = "INVALID_REQUEST";
        if (debug)
        {
            Print("Invalid request format: " + request);
        }
        return;
    }

    command = parts[0];
    subCommand = parts[1];
    ArrayResize(parameters, ArraySize(parts) - 2);
    ArrayCopy(parameters, parts, 0, 2);

    if (debug)
    {
        Print("Parsed request - Command: " + command + ", SubCommand: " + subCommand + ", Parameters: " + StringJoin(parameters, ", "));
    }
}

void BroadcastStreamData(const string &data) {
    for (int i = 0; i < ArraySize(streamingClients); i++) {
        if (streamingClients[i] != NULL && streamingClients[i].IsSocketConnected()) {
            streamingClients[i].Send(data);
        } else {
            Print("Error: Client socket is not connected or is NULL.");
        }
    }
}
