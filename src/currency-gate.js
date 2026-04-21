// Aloria Labs Global Currency & Geo-Location Logic
const GlobalCurrency = {
    current: { code: 'USD', symbol: '$', rate: 1 },
    
    // Core data mapping
    presets: {
        'IN': { code: 'INR', symbol: '₹', rate: 83 },
        'GB': { code: 'GBP', symbol: '£', rate: 0.8 },
        'EU': { code: 'EUR', symbol: '€', rate: 0.92 },
        'US': { code: 'USD', symbol: '$', rate: 1 }
    },

    async init() {
        // 1. Check Cookies first
        let saved = this.getCookie('user_currency');
        if (saved) {
            this.current = JSON.parse(saved);
        } else {
            // 2. Fetch Geo-IP if no cookie
            try {
                const res = await fetch('https://ipapi.co/json/');
                const data = await res.json();
                const country = data.country_code;
                
                if (this.presets[country]) {
                    this.current = this.presets[country];
                } else if (data.continent_code === 'EU') {
                    this.current = this.presets['EU'];
                }
                
                this.setCookie('user_currency', JSON.stringify(this.current), 30);
            } catch (e) {
                console.log("Geo-IP failed, using default USD");
            }
        }
        this.applyCurrency();
    },

    setCookie(name, value, days) {
        const d = new Date();
        d.setTime(d.getTime() + (days*24*60*60*1000));
        let expires = "expires="+ d.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    },

    getCookie(name) {
        let nameEQ = name + "=";
        let ca = document.cookie.split(';');
        for(let i=0;i < ca.length;i++) {
            let c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    },

    applyCurrency() {
        // Update all elements with class 'curr-symbol'
        document.querySelectorAll('.curr-symbol').forEach(el => {
            el.innerText = this.current.symbol;
        });
        // Dispatch event for specialized tools like ROI Predictor
        window.dispatchEvent(new CustomEvent('currencyUpdated', { detail: this.current }));
    }
};

window.addEventListener('DOMContentLoaded', () => GlobalCurrency.init());
