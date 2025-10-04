
const special = ['Medical','Mechanic','IT','Construction','Language'];

export function markerHelper(description) {
    if (special.includes(description)){
        const el = document.createElement('div');
        el.className = description.toLowerCase(); // match CSS class
        el.style.width = '50px';
        el.style.height = '50px';
        return el;
    }
}
