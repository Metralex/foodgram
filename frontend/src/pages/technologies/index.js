import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const Technologies = () => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - Технологии" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Технологии</h1>
      <div className={styles.content}>
        <div>
          <h2 className={styles.subtitle}>Технологии, которые применены в этом проекте:</h2>
          <div className={styles.text}>
            <ul className={styles.textItem}>
              <li className={styles.textItem}>
                <a href="https://www.python.org/downloads/release/python-390/" className={styles.textLink}>Python 3.9</a>
              </li>
              <li className={styles.textItem}>
                <a href="https://docs.djangoproject.com/en/5.1/releases/3.2/" className={styles.textLink}>Django 3.2</a>
              </li>
              <li className={styles.textItem}>
                <a href="https://www.django-rest-framework.org/community/3.0-announcement/" className={styles.textLink}>Django REST Framework 3.13</a>
              </li>
              <li className={styles.textItem}>
              <a href="https://pypi.org/project/djoser/" className={styles.textLink}>Djoser</a>
              </li>
              <li className={styles.textItem}>
                <a href="https://www.postgresql.org/" className={styles.textLink}>PostgreSQL</a>
              </li>
              <li className={styles.textItem}>
                <a href="https://www.docker.com/" className={styles.textLink}>Docker</a>
              </li>
            </ul>
          </div>
        </div>
      </div>

    </Container>
  </Main>
}

export default Technologies

