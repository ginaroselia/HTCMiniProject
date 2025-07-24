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
				const res = await fetch(`http://localhost:5231/request_result?id=${queueId}`);
				const data = await res.json();

				if (!cancelled) {
					if (data?.classification?.prediction) {
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
					setError("Failed to fetch result.");
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
			<div style={{ padding: '2rem' }}>
				<p>No result ID provided.</p>
				<button className="back-button" onClick={() => navigate('/')}>
					Back to Upload
				</button>
			</div>
		);
	}

	if (loading) {
		return (
			<div style={{ padding: '2rem' }}>
				<p>🔄 Waiting for result...</p>
			</div>
		);
	}

	if (error) {
		return (
			<div style={{ padding: '2rem' }}>
				<p>❌ {error}</p>
				<button className="back-button" onClick={() => navigate('/')}>
					Try Again
				</button>
			</div>
		);
	}

	if (!result) {
		return (
			<div style={{ padding: '2rem' }}>
				<p>No result found.</p>
				<button className="back-button" onClick={() => navigate('/')}>
					Back to Upload
				</button>
			</div>
		);
	}

	const { classification, detection } = result;

	return (
		<div style={{ padding: '2rem' }}>
			<h2>🧠 Classification Result</h2>
			<p>
				<strong>Class:</strong> {classification.prediction}
			</p>
			<p>
				<strong>Confidence:</strong> {classification.confidence}%
			</p>

			<h2>🎯 Object Detection</h2>
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
				<div style={{ marginTop: '1rem' }}>
					<h3>🖼 Annotated Image</h3>
					<img
						src={`data:image/jpeg;base64,${detection.image}`}
						alt="Detection"
						style={{ maxWidth: '100%', border: '1px solid #ccc' }}
					/>
				</div>
			)}

			<br />
			<button className="back-button" onClick={() => navigate('/')}>
				🔙 Upload Another
			</button>
		</div>
	);
};

export default Resultpage;
