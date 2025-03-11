// Collection of misc tools for MQL5

// Utility functions for formatting values
string floatMaxString(double val) {
    return (val != DBL_MAX) ? DoubleToString(val, 8) : "";
}

string longMaxString(long val) {
    return (val != LONG_MAX) ? IntegerToString(val) : "";
}

string intMaxString(int val) {
    return (val != INT_MAX) ? IntegerToString(val) : "";
}

bool isAsciiPrintable(string val) {
    for (int i = 0; i < StringLen(val); i++) {
        if (StringGetCharacter(val, i) < 32 || StringGetCharacter(val, i) >= 128) {
            return false;
        }
    }
    return true;
}

string decimalMaxString(double val) {
    return (val != DBL_MAX) ? DoubleToString(val, 8) : "";
}

string StringJoin(const string &arr[], const string &delimiter) {
    string result = "";
    int size = ArraySize(arr);
    for (int i = 0; i < size; i++) {
        result += arr[i];
        if (i < size - 1) {
            result += delimiter;
        }
    }
    return result;
}

string MakeMessage(const string &command, const string &subCommand, const string &parameters[])
{
    string params_str = StringJoin(parameters, "^");
    return command + "^" + subCommand + "^" + params_str;
}

// Helper function to convert bool to string
string BoolToString(bool value)
{
    return value ? "true" : "false";
}

// 
// 
// Helper functions for encoding and compressing strings
// 
// 

// 
// 
// 
// Function to compress a string using a basic run-length encoding (RLE) algorithm
// uchar CompressString(const string &data) {
//     uchar compressed[];
//     int len = StringLen(data);
//     int count = 1;
    
//     for (int i = 0; i < len; i++) {
//         uchar ch = (uchar)StringGetCharacter(data, i);
//         ArrayResize(compressed, ArraySize(compressed) + 1);
//         compressed[ArraySize(compressed) - 1] = ch;
        
//         if (i + 1 < len && StringGetCharacter(data, i) == StringGetCharacter(data, i + 1)) {
//             count++;
//         } else {
//             ArrayResize(compressed, ArraySize(compressed) + 1);
//             compressed[ArraySize(compressed) - 1] = (uchar)count;
//             count = 1;
//         }
//     }
//     return compressed;
// }

// // Function to encode and compress strings
// uchar EncodeStringWithRLECompression(const string &data) {
//     uchar encoded[];
//     uchar compressed[] = CompressString(data);
    
//     for (int i = 0; i < ArraySize(compressed); i++) {
//         uchar ch = compressed[i] + 42;  // Simple shift encoding
//         ArrayResize(encoded, ArraySize(encoded) + 1);
//         encoded[ArraySize(encoded) - 1] = ch;
//     }
//     return encoded;
// }