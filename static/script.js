
const CONFIG = {
    API_URL: 'http://localhost:8000/deals' 
};

const DOM = {
    totalDeals: document.querySelector('#total-deals-val'),
    highPromo: document.querySelector('#high-promo-val'),
    gamesGrid: document.querySelector('.games-grid'),
    refreshBtn: document.querySelector('#refresh-btn'),
    freeDealsVal: document.querySelector('#free-deals-val'),
    cheapestVal: document.querySelector('#cheapest-val')
};


function calculateMaxDiscount(deals) {
    if (!deals || deals.length === 0) return 0;

    const paidDeals = deals.filter(deal => deal.price_now > 0);

    if (paidDeals.length === 0) return 0;

    const discounts = paidDeals.map(deal => deal.savings);
    return Math.round(Math.max(...discounts));
}

function formatCurrency(value) {
    if (value === undefined || value === null || isNaN(value)) return '$0.00';
    return `$${Number(value).toFixed(2)}`;
}

function updateKPIs(deals) {
    if (!deals || deals.length === 0) return;

    DOM.totalDeals.textContent = deals.length;
    DOM.highPromo.textContent = `${calculateMaxDiscount(deals)}%`;

    const paidDeals = deals.filter(deal => deal.price_now > 0);
    if (paidDeals.length > 0) {
        const cheapestPrice = Math.min(...paidDeals.map(deal => deal.price_now));
        DOM.cheapestVal.textContent = formatCurrency(cheapestPrice);
    } else {
        DOM.cheapestVal.textContent = "N/A";
    }

    const freeDealsCount = deals.filter(deal => deal.price_now == 0).length;
    DOM.freeDealsVal.textContent = freeDealsCount;
}

function createGameCardHTML(deal, cheapestPrice) {
    const discount = Math.round(deal.savings);
    const priceNormal = formatCurrency(deal.normal_price);

    let priceText = formatCurrency(deal.price_now);
    let priceClass = "games-price-now";

    if (deal.price_now === 0) {
        priceText = "FREE";
        priceClass = "games-price-now price-free";
        } 
    else if (deal.price_now === cheapestPrice) {
        priceClass = "games-price-now price-cheapest";
        }
    

const coverthumb = deal.thumb;
const fallbackimg = 'https://images.unsplash.com/photo-1560275619-4662e36fa65c?w=300&auto=format&fit=crop';
const redirectUrl = `https://www.cheapshark.com/redirect?dealID=${deal.dealID}`;
const updatedtime = new Date(deal.updated_at).toLocaleDateString('pt-br');

return `
    <article class="games-card">
        <div class="games-wrapper">
            <img 
                src="${coverthumb || fallbackimg}" 
                alt="${deal.title}" 
                class="game-bg" 
                loading="lazy" 
                onerror="this.onerror=null; this.src='${fallbackimg}';" 
            />  
        

            <img 
                src="${coverthumb || fallbackimg}" 
                alt="${deal.title}" 
                class="game-cover" 
       "         loading="lazy" 
                onerror="this.onerror=null; this.src='${fallbackimg}';" 
            />
        </div>

            <div class="games-info">
                <h3 class="games-title">${deal.title}</h3>
            <span class="games-store">${deal.shop || 'Store'}</span>
                <span class="games-steam-string">${deal.steam_rate || 'No Reviews'}</span>
                <span class="games-updated-at">Baited in: ${updatedtime}</span>
                <span class="games-metacritic">Metacritic: ${deal.metacritic ?? 'N/A'}</span>
                <span class="games-critic-steam">Metacritic X Steam: ${deal.critic_steam ?? 'N/A'}</span>
            </div>

            <div class="games-offer">
                <div class="games-offer-price">
                    ${discount > 0 ? `<span class="games-discount">-${discount}%</span>` : ''}
                    <span class="${priceClass}">${priceText}</span>
                    <span class="games-price-normal">${priceNormal}</span>
                </div>
                <div class="games-offer-metrics">
                    <span class="games-sort-rate-price">Score: ${Number(deal.sort_rate_price).toFixed(1)}</span>
                </div>
            </div>

            <a href="${redirectUrl}" target="_blank" rel="noopener noreferrer" class="buy-btn">
                Get Deal
            </a>
        </article>
    `
}

function renderGames(deals) {
    if (!deals || deals.length === 0) {
        DOM.gamesGrid.innerHTML = '<p class="loading">No offers baited.</p>';
        return;
    }

    const paidDeals = deals.filter(deal => deal.price_now > 0);
    const cheapestPrice = paidDeals.length > 0 
        ? Math.min(...paidDeals.map(d => d.price_now)) 
        : null;

    const cardsHTML = deals.map(deal => createGameCardHTML(deal, cheapestPrice)).join('');
    DOM.gamesGrid.innerHTML = cardsHTML;
}


async function fetchDeals() {
    try {
        DOM.gamesGrid.innerHTML = '<p class="loading">Baiting Sharks...</p>';

        const response = await fetch(CONFIG.API_URL);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const deals = await response.json();

        updateKPIs(deals);
        renderGames(deals);

    } catch (error) {
        console.error('Integration error:', error);
        DOM.gamesGrid.innerHTML = '<p class="loading">Issue in contact with backend</p>';
    }
}

function initDashboard() {
    DOM.refreshBtn.addEventListener('click', fetchDeals);
    fetchDeals();
}

document.addEventListener('DOMContentLoaded', initDashboard);