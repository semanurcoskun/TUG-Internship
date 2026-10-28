export async function streamChat(payload, onChunk) {
    const response = await fetch("http://localhost:8000/chat-stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Backend error ${response.status}: ${text}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
                const { value, done } = await reader.read();
                if (done) break; 
                
                const chunk = decoder.decode(value, { stream: true });

                // YENİ VE KUSURSUZ SSE PARSER:
                // Sadece "data: " kelimesinden bölüyoruz. 
                const parts = chunk.split("data: ");
                
                for (let i = 1; i < parts.length; i++) {
                    let text = parts[i];
                    
                    // Python'un her paketin sonuna eklediği gereksiz \n\n karakterlerini siliyoruz
                    if (text.endsWith("\n\n")) {
                        text = text.substring(0, text.length - 2);
                    }
                    
                    if (text === "[DONE]") continue;

                    onChunk(text);
                }
            }
}