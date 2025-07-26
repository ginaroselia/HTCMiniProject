import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';

const Resultpage = () => {
	const { state } = useLocation();
	const navigate = useNavigate();

	const [result, setResult] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	const queueId = state?.result?.queueId;

	useEffect(() => {
		if (!queueId) return;

		let cancelled = false;

		const poll = async () => {
			try {
				const res = await fetch(
					`http://localhost:5231/request_result?id=${queueId}`
				);
				const data = await res.json();

				console.log('API response:', data);

				if (!cancelled) {
					if (data?.message === 'ID not found!') {
						setError('ID not found.');
						setLoading(false);
					} else if (data?.classification?.prediction) {
						setResult(data);
						setLoading(false);
					} else {
						// Try again after delay if result not ready
						setTimeout(poll, 3000);
					}
				}
			} catch (err) {
				console.error(err);
				if (!cancelled) {
					setError('Failed to fetch result.');
					setLoading(false);
				}
			}
		};

		poll(); // initial call

		return () => {
			cancelled = true;
		};
	}, [queueId]);

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

	if (loading) {
		return (
			<div className="result-container-rp">
				<div className="result-card-rp">
					<p>🔄 Waiting for result...</p>
				</div>
			</div>
		);
	}

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
