document.addEventListener("DOMContentLoaded", function () {

    // 1. Setup Tom Select
    new TomSelect("#movie-search", {
        valueField: 'id',
        labelField: 'text',
        searchField: 'text',
        placeholder: "Type a movie name...",

        load: function (query, callback) {
            fetch('/api/movies')
                .then(r => r.json())
                .then(d => callback(d.results))
                .catch(() => callback());
        },

        render: {
            option: function (item, escape) {
                return `<div>
                    <img src="${item.poster}" style="width:25px; vertical-align:middle; margin-right:10px;">
                    <span>${escape(item.text)}</span>
                </div>`;
            },
            item: function (item, escape) {
                return `<div>
                    <span>${escape(item.text)}</span>
                </div>`;
            }
        },

        onChange: function (value) {
            if (!value) return;

            // 1. Transition State (Moves Search Bar to Top)
            document.body.classList.remove('state-initial');

            // 2. Clear & Show Loading
            const grid = document.getElementById('results-grid');
            document.getElementById('results-center-box').classList.remove('hidden');
            grid.innerHTML = '<div style="color:#fff; grid-column:span 5; text-align:center; margin-top:20px;">Computing Match Scores...</div>';

            // 3. Fetch Data
            fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ movie_id: value })
            })
                .then(r => r.json())
                .then(data => {
                    let html = '';

                    if (!data.recommendations.length) {
                        grid.innerHTML = '<div style="grid-column:span 5; text-align:center;">No results found.</div>';
                        return;
                    }

                    data.recommendations.forEach(m => {
                        // Clean Title
                        let title = m.title.replace(/\s\(\d{4}\)$/, '');
                        let yearMatch = m.title.match(/\((\d{4})\)$/);
                        let year = yearMatch ? yearMatch[1] : '';

                        html += `
                        <div class="movie-card">
                            <div class="card-base">
                                <img src="${m.poster}" class="card-poster">
                                <div class="card-meta">
                                    <h4 class="card-title">${title}</h4>
                                    <div class="card-year">${year}</div>
                                </div>
                            </div>
                            
                            <div class="card-drawer">
                                <div class="drawer-content">
                                    <h5 style="margin:0 0 10px 0; color:#000; font-weight:bold;">${title}</h5>
                                    <p class="drawer-overview">${m.overview}</p>
                                </div>
                                <a href="${m.url}" target="_blank" class="drawer-btn">
                                    View on TMDB (${m.score}%)
                                </a>
                            </div>
                        </div>
                    `;
                    });
                    grid.innerHTML = html;
                });
        }
    });
});