import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import './App.css';
import HomePage from './pages/HomePage';
import Resultpage from './pages/Resultpage';

function App() {
	return (
		<>
			<BrowserRouter>
				<Routes>
					<Route path="/" element={<HomePage />} />
					<Route path="/results" element={<Resultpage />} />
				</Routes>
			</BrowserRouter>
		</>
	);
}

export default App;
