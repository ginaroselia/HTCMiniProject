import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Form = () => {
	const [file, setFile] = useState(null);
	const [id, setId] = useState('');

	const navigate = useNavigate();

	// Change the url
	const BASE_URL = 'http://localhost:3000';

	const handleImageChange = (e) => {
		setFile(e.target.files[0]);
	};

	// add the url endpoint
	const handleImageSubmit = async (e) => {
		e.preventDefault();
		if (!file) {
			alert('Please upload an image.');
			return;
		}

		const formData = new FormData();
		formData.append('image', file);

		try {
			const response = await fetch(`${BASE_URL}`, {
				method: 'POST',
				body: formData,
			});
			const result = await response.json();

			navigate('/results', { state: { result } });
		} catch (error) {
			console.error(error);
			alert('Upload failed. Please try again.');
		}
	};

	// add the url endpoint
	const handleIdSubmit = async (e) => {
		e.preventDefault();

		try {
			const response = await fetch(`${BASE_URL}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ id }),
			});
			const result = await response.json();

			navigate('/results', { state: { result } });
		} catch (error) {
			console.error(error);
			alert('No result found for this ID.');
		}
	};

	return (
		<>
			<form onSubmit={handleImageSubmit}>
				<div>
					<label>Upload an image:</label>
					<input type="file" accept="image/*" onChange={handleImageChange} />
				</div>
				{/* 
				<div>
					<label>Select one</label>
					<select>
						<option value="imageClassification">Image Classification</option>
						<option value="objectDetection">Object Detection</option>
					</select>
				</div> */}

				<div>
					<button type="submit">Upload Image</button>
				</div>
			</form>

			<form onSubmit={handleIdSubmit}>
				<div>
					<label>Enter ID:</label>
					<input
						type="text"
						placeholder="Enter ID"
						value={id}
						onChange={(e) => setId(e.target.value)}
					/>
				</div>
				<div>
					<button type="submit">Submit ID</button>
				</div>
			</form>
		</>
	);
};

export default Form;
