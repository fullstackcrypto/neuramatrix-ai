document.querySelectorAll('.zone').forEach(zone => {
    zone.addEventListener('mouseenter', () => {
        zone.style.transform = 'scale(1.1)';
        zone.style.boxShadow = '0 0 20px #66fcf1';
    });
    zone.addEventListener('mouseleave', () => {
        zone.style.transform = 'scale(1)';
        zone.style.boxShadow = 'none';
    });
    zone.addEventListener('click', () => {
        window.location.href = 'services.html';
    });
});