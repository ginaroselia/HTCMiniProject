import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

const Resultpage = () => {
	// Get the state passed from Form page (when using navigate('/results', { state }))
	const { state } = useLocation();

	// Hook that allows us to go back to the upload page
	const navigate = useNavigate();

	// State variables to store result data, loading status, and error messages
	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	// Get the queueId passed from the Form page
	// This ID is used to fetch the result from the backend
	const queueId = state?.result?.queueId;

	// This useEffect runs when the page loads (or when queueId changes)
	useEffect(() => {
		// If there is no queueId, return
		if (!queueId) return;

		// Use to stop polling if component unmounts
		let cancelled = false;

		// Define a function to keep checking backend for result
		const poll = async () => {
			try {
				// Send request to backend with the queueId
				const res = await fetch(
					`http://localhost:5231/request_result?id=${queueId}`
				);

				// Convert the response to JSON
				const data = await res.json();

				console.log('API response:', data); // Log result for debugging

				if (!cancelled) {
					// If backend says ID is not found, show error
					if (data?.message === 'ID not found!') {
						setError('ID not found.');
						setLoading(false);
					}
					// If classification result is available, set the result and stop loading
					if (data?.classification?.prediction) {
						setResult(data);
						setLoading(false);
					} else {
						// Try again after delay if result not ready
						setTimeout(poll, 3000);
					}
				}
			} catch (err) {
				// Handle any error that occurs while fetching
				console.error(err);
				if (!cancelled) {
					setError('Failed to fetch result.');
					setLoading(false);
				}
			}
		};

		poll(); // Start polling immediately when page loads

		// Cleanup: If user leaves the page, stop polling
		return () => {
			cancelled = true;
		};
	}, [queueId]); // Rerun if queueId changes

	// If no queueId is passed, show message and back button
	if (!queueId) {
		return (
			<div className="result-container-rp">
				<div className="result-card-rp">
					<p>No result ID provided.</p>
					<button className="back-button" onClick={() => navigate('/')}>
						Back to Upload
					</button>
				</div>
			</div>
		);
	}

	// Show loading message, while waiting for result
	if (loading) {
		return (
			<div className="result-container-rp">
				<div className="result-card-rp">
					<p>🔄 Waiting for result...</p>
				</div>
			</div>
		);
	}

	// If there is an error, show error message
	if (error) {
		return (
			<div className="result-container-rp">
				<div className="result-card-rp">
					<p>{error}</p>
					<button className="back-button" onClick={() => navigate('/')}>
						Try Again
					</button>
				</div>
			</div>
		);
	}

	// If no error and not loading, but still no result
	if (!result) {
		return (
			<div className="result-container-rp">
				<div className="result-card-rp">
					<p>No result found.</p>
					<button className="back-button" onClick={() => navigate('/')}>
						Back to Upload
					</button>
				</div>
			</div>
		);
	}

	const { classification, detection } = result;

	return (
		<div className="result-container-rp">
			<div className="result-card-rp">
				<h2>Result ID: {queueId}</h2>
				<h3>📊 Classification Result</h3>
				<p>
					<strong>Class:</strong> {classification.prediction}
				</p>
				<p>
					<strong>Confidence:</strong> {classification.confidence}%
				</p>

				<h3>🎯 Object Detection</h3>
				{detection.objects.length > 0 ? (
					<ul>
						{detection.objects.map((item, idx) => (
							<li key={idx}>
								<strong>{item.label}</strong> — {item.confidence}%
							</li>
						))}
					</ul>
				) : (
					<p>No objects detected.</p>
				)}

				{detection.image && (
					<div>
						<h3>Annotated Image</h3>
						<img
							src={`data:image/jpeg;base64,${detection.image}`}
							alt="Detection"
							className="detection-image-rp"
						/>
					</div>
				)}

				<br />
				<button className="back-button" onClick={() => navigate('/')}>
					🔙 Upload Another
				</button>
			</div>
		</div>
	);
};

export default Resultpage;
