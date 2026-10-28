export const getLocalDate = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const getLocalTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
};

export const getUTCDate = () => {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

export const getUTCTime = () => {
    const now = new Date();
    const hours =  String(now.getUTCHours()).padStart(2, '0');
    const minutes  = String(now.getUTCMinutes()).padStart(2, '0');
    const seconds = String(now.getUTCSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
}

// dateUtils.js (Mevcut kodların en altına ekle)

// Backend'den gelen UTC string'ini (örn: "2026-08-09 18:00:00") Local saate çevirir
export const formatTimeForDisplay = (utcString, timeMode) => {
  if (!utcString || utcString === 'Unknown') return utcString;

  // Gelen metni standart ISO formatına (Z=UTC) çeviriyoruz ki JavaScript doğru anlasın
  const safeString = utcString.replace(' ', 'T') + 'Z';
  const dateObj = new Date(safeString);

  // Eğer kullanıcı Local seçtiyse kendi saatine çevirip döndürüyoruz
  if (timeMode === "Local") {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    const hours = String(dateObj.getHours()).padStart(2, '0');
    const minutes = String(dateObj.getMinutes()).padStart(2, '0');
    const seconds = String(dateObj.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } 
  
  // Eğer UTC seçtiyse backend'den geldiği gibi (dokunmadan) döndür
  return utcString;
};