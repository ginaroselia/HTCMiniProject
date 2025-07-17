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

	const { id, prediction, confidence, detection, image_path } = state.result;

	return (
		<div style={{ padding: '2rem' }}>
			<h2>
				🧾 Result ID: <code>{id}</code>
			</h2>
			<h2>🧠 Classification Result</h2>
			<p>
				<strong>Class:</strong> {prediction}
			</p>
			<p>
				<strong>Confidence:</strong> {confidence}%
			</p>

			<h2>🎯 Object Detection</h2>
			{detection?.length > 0 ? (
				<ul>
					{detection.map((item, idx) => (
						<li key={idx}>
							<strong>{item.class}</strong> —{' '}
							{(item.confidence * 100).toFixed(1)}%
						</li>
					))}
				</ul>
			) : (
				<p>No objects detected.</p>
			)}

			{image_path && (
				<div style={{ marginTop: '1rem' }}>
					<h3>🖼 Annotated Image</h3>
					<img
						src={image_path}
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
