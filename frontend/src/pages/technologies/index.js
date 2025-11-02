import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  
  const technologies = [
    { name: 'Django', version: '4.2.16', description: 'Core Django' },
    { name: 'Django REST Framework', version: '3.15.2', description: 'Django REST Framework' },
    { name: 'Djoser', version: '2.2.2', description: 'Authentication' },
    { name: 'psycopg', version: '3.2.3', description: 'Database' },
    { name: 'django-filter', version: '24.2', description: 'Filtering' },
    { name: 'Pillow', version: '10.4.0', description: 'Image processing' },
    { name: 'Gunicorn', version: '23.0.0', description: 'WSGI server' },
    { name: 'requests', version: '2.32.3', description: 'HTTP requests' },
    { name: 'python-dotenv', version: '1.0.1', description: 'Environment variables' },
    { name: 'drf-extra-fields', version: '3.7.0', description: 'Additional DRF fields' },
    { name: 'django-extensions', version: '3.2.3', description: 'Django extensions' },
  ]
  
  return <Main>
    <MetaTags>
      <title>Технологии</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="Технологии" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
          <div className={styles.text}>
            <ul className={styles.textItem}>
              {technologies.map((tech, index) => (
                <li key={index} className={styles.textItem}>
                  <strong>{tech.name}</strong> {tech.version} - {tech.description}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      
    </Container>
  </Main>
}

export default Technologies

