import { useEffect, useState } from "react";
import { MapController } from "./components/MapController/MapController";
import "./App.scss";

function App() {
	const [isDarkMode, setIsDarkMode] = useState(() => {
		if (typeof window === "undefined") {
			return false;
		}
		return window.matchMedia("(prefers-color-scheme: dark)").matches;
	});

	useEffect(() => {
		const theme = isDarkMode ? "dark" : "light";
		document.documentElement.setAttribute("data-theme", theme);
	}, [isDarkMode]);

	return (
		<div className="app">
			<button
				className="theme-toggle"
				type="button"
				onClick={() => setIsDarkMode((current) => !current)}
				aria-pressed={isDarkMode}
			>
				{isDarkMode ? "Light mode" : "Dark mode"}
			</button>
			<MapController />
		</div>
	);
}

export default App;
