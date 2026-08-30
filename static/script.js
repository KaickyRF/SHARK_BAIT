
const CONFIG = {
    API_URL: 'http://localhost:8000/deals' 
};

const DOM = {
    totalDeals: document.querySelector('#total-deals-val'),
    highPromo: document.querySelector('#high-promo-val'),
    gamesGrid: document.querySelector('.games-grid'),
    refreshBtn: document.querySelector('#refresh-btn')
};


function calculateDiscountPercent(normalPrice, priceNow) {
    if (!normalPrice || normalPrice <= 0) return 0;
    const discount = ((normalPrice - priceNow) / normalPrice) * 100;
    return Math.max(0, Math.round(discount));
}

function calculateMaxDiscount(deals) {
    if (!deals || deals.length === 0) return 0;

    const discounts = deals.map(deal => 
        calculateDiscountPercent(deal.normal_price, deal.price_now)
    );

    return Math.max(...discounts);
}

function formatCurrency(value) {
    if (value === undefined || value === null || isNaN(value)) return '$0.00';
    return `$${Number(value).toFixed(2)}`;
}


function updateKPIs(deals) {
    DOM.totalDeals.textContent = deals.length;
    DOM.highPromo.textContent = `${calculateMaxDiscount(deals)}%`;
}

function createGameCardHTML(deal) {
    const discount = calculateDiscountPercent(deal.normal_price, deal.price_now);
    const priceNow = formatCurrency(deal.price_now);
    const priceOld = formatCurrency(deal.normal_price);
    
    // Fallback para capa padrão e link redirecionador
    const coverUrl = `https://www.cheapshark.com/landing?dealID=${deal.dealID}`;
    const redirectUrl = `https://www.cheapshark.com/redirect?dealID=${deal.dealID}`;

    return `
        <article class="games-card">
            <img src="${coverUrl}" alt="${deal.title}" class="game-cover" loading="lazy" />

            <div class="games-info">
                <h3 class="games-title">${deal.title}</h3>
                <span class="games-store">${deal.shop || 'Store'}</span>
                <span class="games-steam-string">${deal.steam_rate || 'No Reviews'}</span>
                <span class="games-metacritic">Metacritic: ${deal.metacritic ?? 'N/A'}</span>
            </div>

            <div class="games-offer">
                <div class="games-offer-price">
                    ${discount > 0 ? `<span class="games-discount">-${discount}%</span>` : ''}
                    <span class="games-price-now">${priceNow}</span>
                    <span class="games-price-normal">${priceOld}</span>
                </div>
                <div class="games-offer-metrics">
                    <span class="games-critic-steam">Score: ${deal.critic_steam}</span>
                </div>
            </div>

            <a href="${redirectUrl}" target="_blank" rel="noopener noreferrer" class="buy-btn">
                Get Deal
            </a>
        </article>
    `;
}

function renderGames(deals) {
    if (!deals || deals.length === 0) {
        DOM.gamesGrid.innerHTML = '<p class="loading">Nenhuma oferta disponível no momento.</p>';
        return;
    }

    const cardsHTML = deals.map(deal => createGameCardHTML(deal)).join('');
    DOM.gamesGrid.innerHTML = cardsHTML;
}


async function fetchDeals() {
    try {
        DOM.gamesGrid.innerHTML = '<p class="loading">Baiting Sharks...</p>';

        const response = await fetch(CONFIG.API_URL);

        if (!response.ok) {
            throw new Error(`Erro na API: ${response.status}`);
        }

        const deals = await response.json();

        updateKPIs(deals);
        renderGames(deals);

    } catch (error) {
        console.error('Erro na integração:', error);
        DOM.gamesGrid.innerHTML = '<p class="loading">Ops! Falha ao conectar com o backend local.</p>';
    }
}

function initDashboard() {
    DOM.refreshBtn.addEventListener('click', fetchDeals);
    fetchDeals();
}

document.addEventListener('DOMContentLoaded', initDashboard);