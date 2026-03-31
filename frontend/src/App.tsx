import { useEffect, useMemo, useState } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import { MapController } from "./components/MapController/MapController";
import { RadioViewer } from "./components/RadioViewer";
import "./App.scss";

function App() {
	const [isDarkMode, setIsDarkMode] = useState(() => {
		if (typeof window === "undefined") {
			return false;
		}
		return window.matchMedia("(prefers-color-scheme: dark)").matches;
	});

	// Keep CSS variables in sync
	useEffect(() => {
		const theme = isDarkMode ? "dark" : "light";
		document.documentElement.setAttribute("data-theme", theme);
	}, [isDarkMode]);

	// Keep MUI in sync
	const muiTheme = useMemo(
		() =>
			createTheme({
				palette: {
					mode: isDarkMode ? "dark" : "light",
				},
			}),
		[isDarkMode]
	);

	return (
		<ThemeProvider theme={muiTheme}>
			<CssBaseline />
			<div className="app">
				<button
					className="theme-toggle"
					type="button"
					onClick={() => setIsDarkMode((current) => !current)}
					aria-pressed={isDarkMode}
				>
					{isDarkMode ? "Light mode" : "Dark mode"}
				</button>

				<div className="app-content">
					<MapController />
					<RadioViewer />
				</div>
			</div>
		</ThemeProvider>
	);
}

export default App;
