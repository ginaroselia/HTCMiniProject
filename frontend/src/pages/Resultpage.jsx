import { useLocation, useNavigate } from 'react-router-dom';

const Resultpage = () => {
	const { state } = useLocation();
	const navigate = useNavigate();

	if (!state || !state.result) {
		return (
			<div style={{ padding: '2rem' }}>
				<p>No result found.</p>
				<button className="back-button" onClick={() => navigate('/')}>
					Back to Upload
				</button>
			</div>
		);
	}

	const { classification, detection } = state.result;

	return (
		<div style={{ padding: '2rem' }}>
			<h2>{/* 🧾 Result ID: <code>{id}</code> */}</h2>
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

			{/* Image Section */}
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
