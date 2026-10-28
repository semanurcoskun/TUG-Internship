import {useState, useRef, useEffect} from "react";
import LoadingOverlay from "./LoadingOverlay";
import {streamChat} from "./stream";
import ReactMarkdown from "react-markdown";

function AskBox ({location, night, rankedTargets}) {
    const [question, setQuestion] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const chatHistoryRef = useRef(null);
    const [isStreaming, setIsStreaming] = useState(false);

    useEffect(() => {
        if (chatHistoryRef.current) {
            chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
        }
    }, [messages]);

    const handleAsk = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;

        setLoading(true);
        setIsStreaming(true);
        setError(null);

        const newUserMessage = {role: "user", content: question};
        const newMessages = [...messages, newUserMessage, { role: "assistant", content: "" }];
        setMessages(newMessages);
        setQuestion("");

        // try {
        //     const res = await fetch("http://localhost:8000/api/ask", {
        //         method: "POST",
        //         headers: {"Content-Type": "application/json"},
        //         body: JSON.stringify({question, location, night, ranked_targets: rankedTargets, history: messages}),
        //     });

        //     const data = await res.json();

        //     if (data.error) {
        //         setError(data.error);
        //     } else{
        //         setMessages([...messages, newUserMessage, {role: "assistant", content: data.answer}]);
        //     }
        // } catch(err) {
        //     setError(err.message);
        // } finally {
        //     setLoading(false);
        // }

        try {
            await streamChat(
                {question, location, night, ranked_targets: rankedTargets, history: messages},
                (piece) => {
                    // if (!firstChunkReceived) {
                    // firstChunkReceived = true;
                    // setLoading(false); // ilk parça gelir gelmez overlay kalksın
                    // }
                    setMessages((prev) => {
                        const updated = [...prev];
                        const lastIndex = updated.length - 1;
                        updated[lastIndex] = {
                            ...updated[lastIndex],
                            content: updated[lastIndex].content + piece,
                        };
                        if (updated.length < 3) {
                            setLoading(false);
                        } 
                        return updated;
                    });
                }
            );
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
            setIsStreaming(false);
        }
    };

    return (
        <div className="ask-box">
            {loading && <LoadingOverlay text="Thinking... Please wait."/>}
            <h2>Ask a question</h2>

            <div className="chat-history" ref={chatHistoryRef}>
                {messages.map((m, i) => (
                <div key={i} className={`chat-message ${m.role}`}>
                    <ReactMarkdown>
                        {/* Llama'nın gönderdiği her alt satır komutunun (\n) önüne 
                            iki adet boşluk ("  ") ekliyoruz ki Markdown bunu alt satır olarak kabul etsin */}
                        {m.content.replace(/\n/g, "  \n")}
                    </ReactMarkdown>
                </div>
                ))}
            </div>

            <form onSubmit={handleAsk}>
                <input
                    type="text"
                    value = {question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Enter your question..."
                />
                <button type="submit" disabled={loading}>
                    {loading ? "Asking..." : "Ask me"}
                </button>
            </form>
            {error && <p className="ask-error">{error}</p>}
        </div>
    );
}

export default AskBox;