
// Import PNG icons for SKILLS category
import MedicalIcon from '../assets/icons/Medical.png';
import MechanicIcon from '../assets/icons/Mechanic.png';
import ITIcon from '../assets/icons/IT.png';
import ConstructionIcon from '../assets/icons/Construction.png';
import LanguageIcon from '../assets/icons/Language.png';
import PersonIcon from '../assets/icons/Person.png';

// Available PNG icons for SKILLS category
const skillsIcons = {
    'MEDICAL': MedicalIcon,
    'MECHANIC': MechanicIcon, 
    'IT': ITIcon,
    'CONSTRUCTION': ConstructionIcon,
    'LANGUAGE': LanguageIcon,
    'OTHER': PersonIcon // Using Person.png for Other skills
};

export function markerHelper(category, subcategory) {
    const el = document.createElement('div');
    el.style.width = '50px';
    el.style.height = '50px';
    el.style.borderRadius = '50%';
    el.style.border = '3px solid #ffffff';
    el.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.3)';
    
    // Handle SKILLS category with PNG icons based on subcategory
    if (category === 'SKILLS' && subcategory && skillsIcons[subcategory]) {
        console.log('Creating PNG marker for:', subcategory);
        const iconPath = skillsIcons[subcategory];
        el.style.backgroundImage = `url(${iconPath})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
        el.style.backgroundRepeat = 'no-repeat';
        console.log('Icon path:', iconPath);
        return el;
    }
    
    // Handle other categories with colored circles and emoji icons
    const categoryColors = {
        'FUEL': '#ff6b35',
        'FOOD': '#f7931e',
        'WATER': '#00b4d8',
        'MEDICAL_SUPPLIES': '#e74c3c',
        'SHELTER': '#8e44ad',
        'TRANSPORT': '#34495e',
        'EQUIPMENT': '#95a5a6',
        'COMMUNICATION': '#3498db',
        'OTHER': '#7f8c8d'
    };
    
    // Set background color based on category
    el.style.backgroundColor = categoryColors[category] || '#7f8c8d';
    el.style.display = 'flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';
    el.style.color = '#ffffff';
    el.style.fontSize = '1.2em';
    el.style.fontWeight = 'bold';
    
    // Add category icon
    const categoryIcons = {
        'FUEL': '⛽',
        'FOOD': '🍽️',
        'WATER': '💧',
        'MEDICAL_SUPPLIES': '🏥',
        'SHELTER': '🏠',
        'TRANSPORT': '🚗',
        'EQUIPMENT': '🔧',
        'COMMUNICATION': '📡',
        'OTHER': '📦'
    };
    
    el.textContent = categoryIcons[category] || '📦';
    
    return el;
}
