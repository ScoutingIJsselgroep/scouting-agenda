const { createApp } = Vue;
const { createVuetify } = Vuetify;

const vuetify = createVuetify({
    theme: {
        themes: {
            light: {
                colors: {
                    primary: '#0C40AA',
                    secondary: '#FCDD07',
                }
            }
        }
    }
});

const logoMap = {
    'bevers': '/static/bevers_RGB.jpg',
    'welpen': '/static/welpen_RGB.jpg',
    'scouts': '/static/scouts_RGB.jpg',
    'explorers': '/static/explorers_RGB.jpg',
    'roverscouts': '/static/roverscouts_RGB.jpg'
};

const app = createApp({
    data() {
        return {
            calendars: window.CALENDARS_DATA || [],
            baseUrl: window.location.origin,
            activeTab: null,
            calendarEvents: {},
            subscribeDialog: false,
            eventDialog: false,
            selectedCalendar: null,
            selectedEvent: null,
            subscribeUrl: '',
            snackbar: false,
            snackbarText: '',
            snackbarColor: 'success',
            viewMode: 'list',
            currentMonth: new Date(),
            dayEventsDialog: false,
            selectedDayEvents: []
        };
    },
    computed: {
        currentMonthLabel() {
            return this.currentMonth.toLocaleDateString('nl-NL', { month: 'long', year: 'numeric' });
        },
        calendarDays() {
            const year = this.currentMonth.getFullYear();
            const month = this.currentMonth.getMonth();

            // First day of month
            const firstDay = new Date(year, month, 1);
            // Last day of month
            const lastDay = new Date(year, month + 1, 0);

            // Get day of week (0 = Sunday, adjust to Monday = 0)
            let startDay = firstDay.getDay() - 1;
            if (startDay === -1) startDay = 6;

            const days = [];
            const events = this.calendarEvents[this.activeTab] || [];

            // Previous month days
            const prevMonthLastDay = new Date(year, month, 0).getDate();
            for (let i = startDay - 1; i >= 0; i--) {
                const day = prevMonthLastDay - i;
                const date = new Date(year, month - 1, day);
                days.push({
                    day,
                    date: date.toISOString(),
                    currentMonth: false,
                    events: this.getEventsForDay(date, events)
                });
            }

            // Current month days
            for (let day = 1; day <= lastDay.getDate(); day++) {
                const date = new Date(year, month, day);
                days.push({
                    day,
                    date: date.toISOString(),
                    currentMonth: true,
                    events: this.getEventsForDay(date, events)
                });
            }

            // Next month days to fill grid
            const remaining = 42 - days.length;
            for (let day = 1; day <= remaining; day++) {
                const date = new Date(year, month + 1, day);
                days.push({
                    day,
                    date: date.toISOString(),
                    currentMonth: false,
                    events: this.getEventsForDay(date, events)
                });
            }

            return days;
        }
    },
    mounted() {
        // Set first tab as active
        if (this.calendars.length > 0) {
            this.activeTab = this.calendars[0].name;
            this.loadEvents(this.calendars[0]);
            this.updateFavicon(this.calendars[0].name);
        }
    },
    watch: {
        activeTab(newVal) {
            // Don't load events for the handleiding tab
            if (newVal === 'handleiding') {
                return;
            }
            const calendar = this.calendars.find(c => c.name === newVal);
            if (calendar && !calendar.protected && !this.calendarEvents[newVal]) {
                this.loadEvents(calendar);
            }
            this.updateFavicon(newVal);
        }
    },
    methods: {
        updateFavicon(calendarName) {
            const favicon = document.getElementById('favicon');
            if (favicon && logoMap[calendarName]) {
                favicon.href = logoMap[calendarName];
            }
        },
        async loadEvents(calendar) {
            if (calendar.protected) return;

            try {
                const url = `${this.baseUrl}/api/events/${calendar.name}`;
                const response = await fetch(url);

                if (!response.ok) throw new Error('Failed to load events');

                const data = await response.json();
                this.calendarEvents[calendar.name] = data.events.map(event => ({
                    ...event,
                    start: new Date(event.start),
                    end: event.end ? new Date(event.end) : new Date(event.start),
                }));
            } catch (error) {
                console.error('Error loading events:', error);
                this.showSnackbar('Fout bij laden van events', 'error');
            }
        },
        showSubscribeDialog(calendar) {
            this.selectedCalendar = calendar;
            const url = `${this.baseUrl}/${calendar.file}`;
            this.subscribeUrl = calendar.protected ? `${url}?key=WACHTWOORD_HIER` : url;
            this.subscribeDialog = true;
        },
        showEvent({ event }) {
            this.selectedEvent = event;
            this.eventDialog = true;
        },
        copyUrl() {
            navigator.clipboard.writeText(this.subscribeUrl).then(() => {
                this.showSnackbar('✅ URL gekopieerd!', 'success');
            }).catch(() => {
                this.showSnackbar('❌ Kopiëren mislukt', 'error');
            });
        },
        formatDate(date) {
            return new Date(date).toLocaleString('nl-NL', {
                weekday: 'short',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        showSnackbar(text, color = 'success') {
            this.snackbarText = text;
            this.snackbarColor = color;
            this.snackbar = true;
        },
        sortedEvents(calendarName) {
            const events = this.calendarEvents[calendarName] || [];
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            return events
                .filter(event => new Date(event.start) >= today)
                .sort((a, b) => new Date(a.start) - new Date(b.start));
        },
        getEventsForDay(date, events) {
            const dayStart = new Date(date);
            dayStart.setHours(0, 0, 0, 0);
            const dayEnd = new Date(date);
            dayEnd.setHours(23, 59, 59, 999);

            return events.filter(event => {
                const eventStart = new Date(event.start);
                const eventEnd = new Date(event.end);
                return (eventStart >= dayStart && eventStart <= dayEnd) ||
                       (eventEnd >= dayStart && eventEnd <= dayEnd) ||
                       (eventStart <= dayStart && eventEnd >= dayEnd);
            });
        },
        previousMonth() {
            this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() - 1);
        },
        nextMonth() {
            this.currentMonth = new Date(this.currentMonth.getFullYear(), this.currentMonth.getMonth() + 1);
        },
        showDayEvents(day) {
            if (day.events.length > 0) {
                this.selectedDayEvents = day.events;
                this.dayEventsDialog = true;
            }
        },
        getLogoPath(calendarName) {
            return logoMap[calendarName] || null;
        }
    }
});

app.use(vuetify);
app.mount('#app');
