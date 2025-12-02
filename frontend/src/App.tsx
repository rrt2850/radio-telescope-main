import { MapControllerAltAz } from "./components/MapControllerAltAz";
import { MapControllerRaDec } from "./components/MapControllerRaDec";

function App() {
	return (
		<>
			<MapControllerRaDec />
			<MapControllerAltAz />
		</>
	);
}

export default App;
