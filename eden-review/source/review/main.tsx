import { createRoot } from "react-dom/client";
import HomePage from "../app/page";
import "../app/globals.css";

window.__EDEN_QA_ENABLED__ = true;
createRoot(document.getElementById("root")!).render(<HomePage />);
