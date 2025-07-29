import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Form = () => {
	// 'file' stores the uploaded image, 'setFile' lets us change it
	const [file, setFile] = useState(null);

	// 'id' stores the ID entered by the user
	const [id, setId] = useState('');

	// This hook helps us move to a different page (like going to result page)
	const navigate = useNavigate();

	// Base URL of our backend server
	const BASE_URL = 'http://localhost:5231';

	// This function runs when user selects a file
	const handleImageChange = (e) => {
		setFile(e.target.files[0]); // Save the selected file into state
	};

	// This  function runs when user clicks "Upload Image"
	const handleImageSubmit = async (e) => {
		e.preventDefault(); // Stop the form from refreshing the page

		// If no image was selected, show an alert
		if (!file) {
			alert('Please upload an image.');
			return;
		}

		// Create a form that includes the uploaded image file
		const formData = new FormData();
		formData.append('image', file); // Attach the image with key "image"

		try {
			// Send the image to the backend using POST method
			const response = await fetch(`${BASE_URL}/upload_img`, {
				method: 'POST',
				body: formData,
			});

			// Read the JSON response from the server
			const result = await response.json();
			console.log(result); // Print the result for debugging

			// Go to the results page and pass the result using 'state'
			navigate('/results', { state: { result } });
		} catch (error) {
			// If something goes wrong, show an error
			console.error(error);
			alert(
				'Error uploading file: Only PNG, JPEG, GIF, or WEBP formats are supported.'
			);
		}
	};

	// This function runs when user enters an ID and clicks "Submit ID"
	const handleIdSubmit = async (e) => {
		e.preventDefault(); // Prevent page refresh

		// Go to the results page, passing only the ID to be used later
		navigate('/results', { state: { result: { queueId: id } } });
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
