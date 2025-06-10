import {StrictMode} from 'react'
import {createRoot} from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import {NotificationsProvider} from "./components/NotificationsProvider"
import {installFetchInterceptor} from "./lib/fetchInterceptor"


installFetchInterceptor();

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <NotificationsProvider><App/></NotificationsProvider>
    </StrictMode>
)
