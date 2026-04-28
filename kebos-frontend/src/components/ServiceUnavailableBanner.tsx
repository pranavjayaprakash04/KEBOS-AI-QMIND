
export function ServiceUnavailableBanner() {
  return (
    <div 
      role="alert" 
      className="service-unavailable-banner"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fef2f2',
        padding: '2rem',
        zIndex: 9999,
      }}
    >
      <div 
        className="icon"
        style={{
          fontSize: '4rem',
          marginBottom: '1rem',
        }}
      >
        ⚠
      </div>
      <div 
        className="message"
        style={{
          fontSize: '1.25rem',
          color: '#991b1b',
          textAlign: 'center',
          maxWidth: '600px',
          lineHeight: '1.6',
        }}
      >
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#7f1d1d' }}>
          Service Temporarily Unavailable
        </h1>
        <p>
          Kebos backend is temporarily unavailable.
          The dashboard will reconnect automatically.
        </p>
        <p style={{ fontSize: '1rem', color: '#6b7280', marginTop: '1rem' }}>
          Please check your connection or try again later.
        </p>
      </div>
    </div>
  );
}
