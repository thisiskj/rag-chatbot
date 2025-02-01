import { useState } from 'react'
import './App.css'
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm";
import LoadingSpinner from './LoadingSpinner';

function App() {
    const [messages, setMessages] = useState([])
    const [loading, setLoading] = useState(false)

    const onSubmit = (e) => {
        e.preventDefault()
        setMessages([])
        setLoading(true)

        const formData = new FormData(e.target);
        // @ts-ignore-error
        const queryString = new URLSearchParams(formData).toString()
        
        const evtSource = new EventSource(`${import.meta.env.VITE_API_URL}/search?${queryString}`, {
            withCredentials: true,
        });

        evtSource.addEventListener("res", (event) => {
            setLoading(false)
            setMessages((prevState) => {
                return [...prevState, event.data]
            })
        });

        evtSource.addEventListener("end", () => {
            evtSource.close()
        });
        
        return () => {
            evtSource.close()
        }
    }

    return (
        <div className="my-8 flex justify-center">
            <div className="w-xl">
                <div className="text-2xl font-bold mb-4">Ask Django</div>
                <form onSubmit={onSubmit}>
                    <div className="mb-4">
                        <input type="text" className="w-full text-sm text-slate-600 bg-white border border-slate-300 appearance-none rounded-lg px-3.5 py-2.5 outline-none focus:bg-white focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100" id="query" name="q" placeholder="Ask me anything about Django" required />
                    </div>
                    <button className="w-full inline-flex justify-center whitespace-nowrap rounded-lg bg-indigo-500 px-3.5 py-2.5 text-sm font-medium text-white shadow-sm shadow-indigo-950/10 hover:bg-indigo-600 focus-visible:outline-none focus-visible:ring focus-visible:ring-indigo-300 dark:focus-visible:ring-slate-600 transition-colors duration-150 group">
                        Go
                    </button>
                </form>
                {loading ? (
                    <div className="text-center my-4">
                        <LoadingSpinner />
                    </div>
                ): (
                    <div className="mt-10 text-left">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {messages.join('')}
                        </ReactMarkdown>
                    </div>
                )}
                
            </div>
        </div>
        
    )
}

export default App
