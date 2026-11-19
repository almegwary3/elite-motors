
import { useEffect, useState } from "react";
import "./App.css";
import carImages from "./carImages";
const API_URL = "https://elite-motors-g5e4.vercel.app";

interface Car {
  id: string;
  brand: string;
  model: string;
  displayName: string;
  searchKey: string;
  year: number | null;
  engine: string | null;
  powerHp: number | null;
  torqueNm: number | null;
  fuelType: string | null;
  transmission: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

function App() {
  const [cars, setCars] = useState<Car[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [selectedCar, setSelectedCar] = useState<Car | null>(null);

  // CHATBOT STATES
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "أهلاً بيك في ELITE MOTORS! 👋 أنا ELITE AI، مساعدك الذكي للسيارات. اسألني عن أي عربية أو مواصفاتها وأنا هساعدك.",
    },
  ]);

  // LOAD CARS FROM BACKEND
  useEffect(() => {
    fetch(`${API_URL}/api/featured-cars`, {
      cache: "no-store",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to load cars");
        }

        return response.json();
      })
      .then((data) => {
        console.log("Backend response:", data);

        const carsList = Array.isArray(data)
          ? data
          : data.cars || data.Cars || data.data?.cars || [];

        setCars(carsList);
      })
      .catch((error) => {
        console.error("Error loading cars:", error);
        setCars([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  // SEND MESSAGE TO AI
  const sendMessage = async () => {
    const message = chatInput.trim();

    if (!message || chatLoading) return;

    // Previous conversation
    const conversationHistory = messages.map((msg) => ({
      role: msg.role,
      content: msg.text,
    }));

    // Display user message
    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        text: message,
      },
    ]);

    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          searchKey: "",
          history: conversationHistory,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || "Something went wrong with the AI"
        );
      }

      const aiReply =
        data.answer ||
        data.reply ||
        data.response ||
        data.message;

      if (!aiReply || typeof aiReply !== "string") {
        throw new Error("The AI returned an unexpected response.");
      }

      // Display AI response
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: aiReply,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text:
            error instanceof Error
              ? `حصلت مشكلة: ${error.message}`
              : "مش قادر أتصل بالـ AI حاليًا. حاول تاني.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const displayedCars = showAll ? cars : cars.slice(0, 3);

  return (
    <div className="website">

      {/* NAVBAR */}
      <nav className="navbar">
        <div className="logo">
          ELITE <span>MOTORS</span>
        </div>

        <div className="nav-links">
          <a href="#home">Home</a>
          <a href="#collection">Collection</a>
          <a href="#about">About</a>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section className="hero" id="home">
        <div className="hero-content">
          <span>WELCOME TO ELITE MOTORS</span>

          <h1>
            DISCOVER YOUR
            <br />
            DREAM CAR
          </h1>

          <p>
            Explore our exclusive collection of luxury and performance cars.
          </p>

          <a href="#collection" className="hero-button">
            EXPLORE COLLECTION
          </a>
        </div>
      </section>

      {/* CAR COLLECTION */}
      <section className="collection" id="collection">
        <div className="section-heading">
          <span>OUR COLLECTION</span>
          <h2>Discover Our Cars</h2>
          <p>Explore our selected collection of vehicles.</p>
        </div>

        {loading ? (
          <p className="loading">Loading cars...</p>
        ) : cars.length === 0 ? (
          <p className="error">
            No cars found. Please check the Backend server.
          </p>
        ) : (
          <>
            <div className="cars-grid">
              {displayedCars.map((car) => (
                <div className="car-card" key={car.id}>
                  {carImages[car.searchKey] ? (
                    <img
                      src={carImages[car.searchKey]}
                      alt={car.displayName}
                      onError={(event) => {
                        event.currentTarget.style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="car-placeholder">
                      <span>ELITE MOTORS</span>
                      <h2>{car.displayName}</h2>
                    </div>
                  )}

                  <div className="car-info">
                    <h3>{car.displayName}</h3>

                    <p>{car.year || "Year unavailable"}</p>

                    <div className="car-bottom">
                      <button onClick={() => setSelectedCar(car)}>
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* VIEW ALL BUTTON */}
            <div className="view-all-container">
              <button
                className="view-all-button"
                onClick={() => setShowAll(!showAll)}
              >
                {showAll ? "SHOW LESS" : "VIEW ALL CARS"}
              </button>
            </div>
          </>
        )}
      </section>

     {/* CAR DETAILS */}
{selectedCar && (
  <div className="modal-overlay">
    <div className="car-modal">

      <button
        className="close-modal"
        onClick={() => setSelectedCar(null)}
      >
        ✕
      </button>

      <div className="details-header">
        <span>ELITE MOTORS</span>
        <h2>{selectedCar.displayName}</h2>
        <p>Vehicle Specifications</p>
      </div>

      <div className="details-list">

        <div className="detail-item">
          <span>📅 Year</span>
          <strong>{selectedCar.year ?? "Not available"}</strong>
        </div>

        <div className="detail-item">
          <span>⚙️ Engine</span>
          <strong>{selectedCar.engine ?? "Not available"}</strong>
        </div>

        <div className="detail-item">
          <span>🏎️ Power</span>
          <strong>{selectedCar.powerHp ?? "Not available"} HP</strong>
        </div>

        <div className="detail-item">
          <span>🔩 Torque</span>
          <strong>{selectedCar.torqueNm ?? "Not available"} Nm</strong>
        </div>

        <div className="detail-item">
          <span>⛽ Fuel</span>
          <strong>{selectedCar.fuelType ?? "Not available"}</strong>
        </div>

        <div className="detail-item">
          <span>🔄 Transmission</span>
          <strong>{selectedCar.transmission ?? "Not available"}</strong>
        </div>

      </div>

      <div className="details-footer">
        PREMIUM AUTOMOTIVE EXPERIENCE
      </div>

    </div>
  </div>
)}

      {/* ABOUT */}
      <section className="about" id="about">
        <div className="section-heading">
          <span>ABOUT US</span>
          <h2>ELITE MOTORS</h2>
        </div>

        <p>
          ELITE MOTORS brings together an exclusive collection
          of vehicles with detailed specifications.
        </p>
      </section>

      {/* FOOTER */}
      <footer>
        <p>© 2026 ELITE MOTORS. All Rights Reserved.</p>
      </footer>

     {/* AI ASSISTANT BUTTON */}
<button
  className="chatbot-button"
  onClick={() => setChatOpen(!chatOpen)}
  title="AI Assistant"
>
  {chatOpen ? "✕" : "AI Assistant"}
</button>
      {/* CHAT WINDOW */}
      {chatOpen && (
        <div
          style={{
            position: "fixed",
            bottom: "105px",
            right: "30px",
            width: "350px",
            maxWidth: "calc(100vw - 40px)",
            height: "450px",
            maxHeight: "65vh",
            background: "#111",
            border: "1px solid #d4af37",
            borderRadius: "12px",
            display: "flex",
            flexDirection: "column",
            zIndex: 999,
            boxShadow: "0 5px 25px rgba(0,0,0,0.5)",
            overflow: "hidden",
          }}
        >

          {/* CHAT HEADER */}
          <div
            style={{
              background: "#d4af37",
              color: "#000",
              padding: "15px",
              fontWeight: "bold",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>ELITE MOTORS AI 🤖</span>
            <span style={{ fontSize: "12px" }}>Online</span>
          </div>

          {/* CHAT MESSAGES */}
          <div
            style={{
              flex: 1,
              padding: "15px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            {messages.map((msg, index) => (
              <div
                key={index}
                dir="auto"
                style={{
                  alignSelf:
                    msg.role === "user" ? "flex-end" : "flex-start",
                  background:
                    msg.role === "user" ? "#d4af37" : "#292929",
                  color:
                    msg.role === "user" ? "#000" : "#fff",
                  padding: "10px 12px",
                  borderRadius: "10px",
                  maxWidth: "85%",
                  fontSize: "14px",
                  lineHeight: "1.6",
                  whiteSpace: "pre-wrap",
                  overflowWrap: "anywhere",
                  textAlign: "start",
                }}
              >
                {msg.text}
              </div>
            ))}

            {/* AI LOADING */}
            {chatLoading && (
              <div
                style={{
                  alignSelf: "flex-start",
                  background: "#292929",
                  color: "#d4af37",
                  padding: "10px 12px",
                  borderRadius: "10px",
                  fontSize: "14px",
                }}
              >
                ELITE AI is thinking...
              </div>
            )}
          </div>

          {/* CHAT INPUT */}
          <form
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage();
            }}
            style={{
              display: "flex",
              gap: "8px",
              padding: "12px",
              borderTop: "1px solid #333",
            }}
          >
            <input
              type="text"
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Ask ELITE AI anything..."
              disabled={chatLoading}
              style={{
                flex: 1,
                minWidth: 0,
                padding: "11px",
                borderRadius: "6px",
                border: "1px solid #555",
                background: "#222",
                color: "#fff",
                outline: "none",
                fontSize: "14px",
              }}
            />

            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              style={{
                background: "#d4af37",
                color: "#000",
                border: "none",
                borderRadius: "6px",
                padding: "0 14px",
                fontWeight: "bold",
                cursor: "pointer",
                opacity:
                  chatLoading || !chatInput.trim() ? 0.5 : 1,
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}

    </div>
  );
}

export default App;
